"""Run lifecycle: consume agent events, derive stages/states, fan out SSE events.

Stages and the final verdict are derived server-side from the observed tool calls and
the engine's real state — never from the model's claims (requirements 8, 20, 27).
"""

import asyncio
import logging
import time
import uuid
from collections.abc import AsyncGenerator, Callable
from typing import Any

from app.agent.callbacks import RunRecord
from app.config import RUN_TIMEOUT_SECONDS
from app.simulation.engine import SimulationEngine
from app.simulation.scenario import BAD_DEPLOY, Scenario

from .events import (
    RUN_STATE_LABELS,
    ErrorPayload,
    ResultPayload,
    RunStatePayload,
    SafetyBlockedPayload,
    SseEvent,
    StagePayload,
    ToolCallPayload,
    ToolResultPayload,
)
from .states import STAGE_LABELS, TERMINAL_STATES, RunState, Stage

logger = logging.getLogger(__name__)

# source(engine, record) -> async generator of ADK events
EventSourceFactory = Callable[[SimulationEngine, RunRecord], AsyncGenerator]

TOOL_STAGES: dict[str, Stage] = {
    "get_metrics": Stage.METRICS,
    "search_logs": Stage.LOGS,
    "get_deploy_history": Stage.DEPLOYS,
    "rollback_revision": Stage.RECOVERY,
}
EVIDENCE_TOOLS = {"get_metrics", "get_deploy_history"}
MAX_REASON_CHARS = 200
MAX_SUMMARY_CHARS = 300


class Run:
    def __init__(self, scenario: Scenario) -> None:
        self.id = uuid.uuid4().hex[:12]
        self.scenario = scenario
        self.engine = SimulationEngine(scenario)
        self.record = RunRecord()
        self.state = RunState.IDLE
        self.stage: Stage | None = None
        self.history: list[SseEvent] = []
        self.subscribers: list[asyncio.Queue] = []
        self.task: asyncio.Task | None = None
        self.started_at = time.monotonic()
        self.closed = False

    # -- event fan-out (synchronous on purpose: no awaits => no subscribe race) --

    def emit(self, type_: str, payload: dict[str, Any]) -> None:
        event = SseEvent(type=type_, payload=payload)
        self.history.append(event)
        for queue in self.subscribers:
            queue.put_nowait(event)

    def subscribe(self) -> tuple[list[SseEvent], asyncio.Queue]:
        queue: asyncio.Queue = asyncio.Queue()
        history = list(self.history)
        if self.closed:
            queue.put_nowait(None)
        else:
            self.subscribers.append(queue)
        return history, queue

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        for queue in self.subscribers:
            queue.put_nowait(None)
        self.subscribers.clear()

    # -- state helpers -----------------------------------------------------

    def set_state(self, state: RunState) -> None:
        if state == self.state:
            return
        self.state = state
        self.emit(
            "run_state", RunStatePayload(state=state, label=RUN_STATE_LABELS[state]).model_dump()
        )

    def set_stage(self, stage: Stage) -> None:
        if stage == self.stage:
            return
        self.stage = stage
        self.emit("stage", StagePayload(stage=stage, label=STAGE_LABELS[stage]).model_dump())

    def emit_system_state(self) -> None:
        self.emit("system_state", self.engine.system_snapshot())


def summarize_tool_result(tool: str, resp: dict[str, Any]) -> str:
    """Compact Japanese fact summary for the UI (requirement 13)."""
    try:
        if "error" in resp:
            return f"不明なサービス指定(利用可能: {', '.join(resp.get('known_services', []))})"
        if resp.get("blocked"):
            return str(resp.get("reason", "安全ポリシーにより拒否されました"))
        if tool == "get_metrics":
            s = resp["summary"]
            base = (
                f"{resp['service']}: エラー率 {s['current_error_rate_pct']}%"
                f"(基準 {s['baseline_error_rate_pct']}%)"
            )
            if s.get("anomaly_started_at"):
                base += f"、{s['anomaly_started_at']} 頃から異常"
            return base
        if tool == "search_logs":
            errors = [e for e in resp["matched"] if e["severity"] in ("ERROR", "WARNING")]
            if not errors:
                return f"{resp['service']}: 異常ログなし({resp['total_matched']}件は正常)"
            first = errors[0]
            return (
                f"{resp['service']}: {first['severity']} {len(errors)}件 — 「{first['message']}」"
            )
        if tool == "get_deploy_history":
            if not resp.get("revisions"):
                return f"{resp['service']}: リビジョン管理対象外"
            current = resp["current_revision"]
            latest = resp["revisions"][0]
            stable = next((r for r in resp["revisions"] if r["stable"]), None)
            base = f"現行 {current}({latest['deployed_at']} デプロイ)"
            if stable and stable["revision"] != current:
                base += f"、安定版 {stable['revision']} へロールバック可能"
            return base
        if tool == "rollback_revision":
            if resp.get("accepted"):
                return (
                    f"{resp['from_revision']} → {resp['to_revision']} へ切り替え({resp['message']})"
                )
            return f"拒否: {resp.get('reason', '不明')}"
        if tool == "check_health":
            names = {
                s["name"]: f"{s['status']}(エラー率 {s['error_rate_pct']}%)"
                for s in resp["services"]
            }
            detail = "、".join(f"{k}: {v}" for k, v in names.items())
            return f"全体: {resp['overall']} — {detail}"
    except (KeyError, IndexError, TypeError):
        logger.exception("failed to summarize tool result for %s", tool)
    return "観測結果を取得しました"


def _normalize_response(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict) and set(raw.keys()) == {"result"} and isinstance(raw["result"], dict):
        return raw["result"]
    return raw if isinstance(raw, dict) else {"value": raw}


class RunManager:
    def __init__(self, event_source_factory: EventSourceFactory | None = None) -> None:
        if event_source_factory is None:
            from .adk_source import adk_event_source

            event_source_factory = adk_event_source
        self._factory = event_source_factory
        self.runs: dict[str, Run] = {}

    def get(self, run_id: str) -> Run | None:
        return self.runs.get(run_id)

    def create_run(self) -> Run:
        run = Run(BAD_DEPLOY)
        self.runs[run.id] = run
        # keep only the most recent runs in memory
        while len(self.runs) > 20:
            oldest_id = next(iter(self.runs))
            old = self.runs.pop(oldest_id)
            if old.task and not old.task.done():
                old.task.cancel()
            old.close()

        run.engine.inject_fault()
        run.set_state(RunState.FAULT_INJECTED)
        run.emit_system_state()
        run.set_stage(Stage.SITUATION)
        run.task = asyncio.create_task(self._run_with_guards(run))
        return run

    def cancel(self, run_id: str) -> bool:
        run = self.get(run_id)
        if run is None:
            return False
        if run.task and not run.task.done():
            run.task.cancel()
        run.close()
        return True

    async def _run_with_guards(self, run: Run) -> None:
        try:
            await asyncio.wait_for(self._consume(run), timeout=RUN_TIMEOUT_SECONDS)
        except TimeoutError:
            self._fail_run(run, "処理時間の上限に達したため実行を停止しました。")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("run %s failed", run.id)
            self._fail_run(run, "内部エラーが発生しました。再実行またはリセットしてください。")
        finally:
            run.close()

    def _fail_run(self, run: Run, message: str) -> None:
        stage_label = STAGE_LABELS.get(run.stage, "状況把握") if run.stage else "状況把握"
        run.emit(
            "error", ErrorPayload(message=message, stopped_stage_label=stage_label).model_dump()
        )
        run.set_state(RunState.EXECUTION_ERROR)

    async def _consume(self, run: Run) -> None:
        engine = run.engine
        record = run.record
        rollback_accepted = False
        verified_after_rollback = False
        any_tool_called = False
        last_reason = ""
        final_text = ""

        async for event in self._factory(engine, record):
            if getattr(event, "partial", False):
                continue
            content = getattr(event, "content", None)
            parts = list(content.parts) if content and content.parts else []
            texts = [p.text.strip() for p in parts if getattr(p, "text", None) and p.text.strip()]
            calls = [p.function_call for p in parts if getattr(p, "function_call", None)]
            responses = [
                p.function_response for p in parts if getattr(p, "function_response", None)
            ]

            for text in texts:
                last_reason = text[:MAX_REASON_CHARS]
                if not any_tool_called:
                    run.set_stage(Stage.PLANNING)
                elif record.called_tools >= EVIDENCE_TOOLS and not rollback_accepted:
                    run.set_stage(Stage.CAUSE)
                    run.set_state(RunState.CAUSE_IDENTIFIED)
                final_text = text

            for call in calls:
                name = call.name or ""
                args = dict(call.args or {})
                any_tool_called = True
                run.emit(
                    "tool_call",
                    ToolCallPayload(tool=name, args=args, reason=last_reason).model_dump(),
                )
                last_reason = ""
                if name in TOOL_STAGES:
                    run.set_stage(TOOL_STAGES[name])
                elif name == "check_health":
                    run.set_stage(Stage.VERIFY if rollback_accepted else Stage.SITUATION)
                if run.state == RunState.FAULT_INJECTED:
                    run.set_state(RunState.INVESTIGATING)

            for response in responses:
                name = response.name or ""
                resp = _normalize_response(response.response)
                blocked = bool(resp.get("blocked"))
                run.emit(
                    "tool_result",
                    ToolResultPayload(
                        tool=name, summary=summarize_tool_result(name, resp), blocked=blocked
                    ).model_dump(),
                )
                if blocked:
                    run.emit(
                        "safety_blocked",
                        SafetyBlockedPayload(
                            tool=name,
                            reason=str(resp.get("reason", "")),
                            blocked_count=record.blocked_count,
                        ).model_dump(),
                    )
                    continue
                if name == "rollback_revision" and resp.get("accepted"):
                    rollback_accepted = True
                    run.set_state(RunState.RECOVERING)
                    run.emit_system_state()
                if name == "check_health" and rollback_accepted:
                    verified_after_rollback = True
                    run.set_state(RunState.VERIFYING)
                    run.emit_system_state()

        # -- final verdict from engine ground truth --------------------------
        run.set_stage(Stage.DONE)
        recovered = engine.phase.value == "recovered"
        success = recovered and verified_after_rollback

        if success:
            verification_summary = "復旧後の check_health で全サービスの正常化を確認しました。"
        elif recovered and not verified_after_rollback:
            verification_summary = (
                "復旧後の正常性検証が実施されなかったため、成功と判定できません。"
            )
        elif rollback_accepted:
            verification_summary = "復旧操作後もシステムが正常状態に戻っていません。"
        else:
            verification_summary = "有効な復旧操作が実行されませんでした。"

        recovery_action = (
            f"{run.scenario.id}: checkout-app を {run.scenario.bad_revision} から "
            f"{run.scenario.good_revision} へロールバック"
            if rollback_accepted
            else "実行されず"
        )
        run.emit(
            "result",
            ResultPayload(
                success=success,
                final_state=RunState.RECOVERED if success else RunState.RECOVERY_FAILED,
                root_cause_summary=final_text[:MAX_SUMMARY_CHARS] or "(最終報告なし)",
                recovery_action=recovery_action,
                verified=verified_after_rollback,
                verification_summary=verification_summary,
                elapsed_seconds=round(time.monotonic() - run.started_at, 1),
                tool_call_count=record.tool_call_count,
                safety_blocked_count=record.blocked_count,
            ).model_dump(),
        )
        run.set_state(RunState.RECOVERED if success else RunState.RECOVERY_FAILED)
        run.emit_system_state()


def is_terminal(state: RunState) -> bool:
    return state in TERMINAL_STATES
