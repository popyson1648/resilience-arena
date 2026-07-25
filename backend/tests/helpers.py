"""Scripted fake event sources that mimic the ADK Runner without calling Gemini.

The fake source executes the real guardrail and the real tools against the run's
engine, so orchestrator tests exercise genuine state transitions.
"""

from types import SimpleNamespace

from google.adk.events import Event
from google.genai import types

from app.agent.callbacks import RunRecord, build_guardrail
from app.agent.tools import build_tools
from app.simulation.engine import SimulationEngine
from app.simulation.scenario import APP

AUTHOR = "sre_responder"


def text_event(text: str) -> Event:
    return Event(author=AUTHOR, content=types.Content(role="model", parts=[types.Part(text=text)]))


def call_event(name: str, args: dict) -> Event:
    part = types.Part(function_call=types.FunctionCall(name=name, args=args))
    return Event(author=AUTHOR, content=types.Content(role="model", parts=[part]))


def response_event(name: str, response: dict) -> Event:
    part = types.Part(function_response=types.FunctionResponse(name=name, response=response))
    return Event(author=AUTHOR, content=types.Content(role="user", parts=[part]))


class ToolExecutor:
    """Runs the real guardrail + tool, exactly like the ADK runner would."""

    def __init__(self, engine: SimulationEngine, record: RunRecord) -> None:
        self.guardrail = build_guardrail(record)
        self.tools = {fn.__name__: fn for fn in build_tools(engine)}

    def execute(self, name: str, args: dict) -> dict:
        blocked = self.guardrail(SimpleNamespace(name=name), dict(args), None)
        if blocked is not None:
            return blocked
        return self.tools[name](**args)


async def scripted_run(engine, record, steps):
    """steps: list of ('text', str) or ('tool', name, args)."""
    executor = ToolExecutor(engine, record)
    for step in steps:
        if step[0] == "text":
            yield text_event(step[1])
        else:
            _, name, args = step
            yield call_event(name, args)
            yield response_event(name, executor.execute(name, args))


HAPPY_STEPS = [
    ("text", "まず全体の正常性とメトリクスを確認します。"),
    ("tool", "check_health", {"service": "all"}),
    ("tool", "get_metrics", {"service": APP, "window_minutes": 30}),
    ("text", "エラー率が急上昇しています。ログとデプロイ履歴で裏取りします。"),
    ("tool", "search_logs", {"service": APP, "window_minutes": 30, "query": "error"}),
    ("tool", "get_deploy_history", {"service": APP}),
    ("text", "10:31 の rev-002 デプロイ直後からエラーが発生しており、設定不備が原因と判断します。"),
    ("tool", "rollback_revision", {"service": APP, "target_revision": "rev-001"}),
    ("tool", "check_health", {"service": "all"}),
    (
        "text",
        "原因: rev-002 の設定不備\n実施した操作: rev-001 へロールバック\n検証結果: 全サービス正常",
    ),
]
