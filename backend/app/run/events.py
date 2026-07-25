"""SSE event schemas. Mirror any change in frontend/src/api/events.ts."""

from typing import Any, Literal

from pydantic import BaseModel

from .states import RunState, Stage


class SseEvent(BaseModel):
    type: str
    payload: dict[str, Any]


class RunStatePayload(BaseModel):
    state: RunState
    label: str


class StagePayload(BaseModel):
    stage: Stage
    label: str


class ToolCallPayload(BaseModel):
    tool: str
    args: dict[str, Any]
    reason: str


class ToolResultPayload(BaseModel):
    tool: str
    summary: str
    blocked: bool = False


class SafetyBlockedPayload(BaseModel):
    tool: str
    reason: str
    blocked_count: int


class ResultPayload(BaseModel):
    success: bool
    final_state: RunState
    root_cause_summary: str
    recovery_action: str
    verified: bool
    verification_summary: str
    elapsed_seconds: float
    tool_call_count: int
    safety_blocked_count: int


class ErrorPayload(BaseModel):
    message: str
    stopped_stage_label: str


RUN_STATE_LABELS: dict[RunState, str] = {
    RunState.IDLE: "待機中",
    RunState.FAULT_INJECTED: "障害発生",
    RunState.INVESTIGATING: "調査中",
    RunState.CAUSE_IDENTIFIED: "原因特定",
    RunState.RECOVERING: "復旧操作中",
    RunState.VERIFYING: "検証中",
    RunState.RECOVERED: "復旧完了",
    RunState.RECOVERY_FAILED: "復旧失敗",
    RunState.EXECUTION_ERROR: "実行エラー",
}

EventType = Literal[
    "snapshot",
    "run_state",
    "stage",
    "system_state",
    "tool_call",
    "tool_result",
    "safety_blocked",
    "result",
    "error",
]
