"""Guardrails enforced deterministically outside the model (before_tool_callback)."""

from dataclasses import dataclass, field
from typing import Any

from .tools import ALLOWED_TOOLS, ROLLBACK_EVIDENCE_TOOLS


@dataclass
class RunRecord:
    """Per-run facts shared between the guardrail and the orchestrator."""

    called_tools: set[str] = field(default_factory=set)
    tool_call_count: int = 0
    blocked_count: int = 0


def evaluate_tool_call(record: RunRecord, tool_name: str) -> str | None:
    """Return a block reason, or None to allow. Pure logic, unit-testable."""
    if tool_name not in ALLOWED_TOOLS:
        return f"ツール '{tool_name}' は許可リストに含まれていません。"
    if tool_name == "rollback_revision":
        missing = ROLLBACK_EVIDENCE_TOOLS - record.called_tools
        if missing:
            return (
                "復旧操作の前に観測による根拠が必要です。"
                f"未実施の調査: {', '.join(sorted(missing))}。"
                "メトリクスとデプロイ履歴を確認してから再度実行してください。"
            )
    return None


def build_guardrail(record: RunRecord):
    def guardrail(tool, args: dict[str, Any], tool_context) -> dict | None:  # noqa: ARG001
        reason = evaluate_tool_call(record, tool.name)
        if reason is not None:
            record.blocked_count += 1
            return {"blocked": True, "reason": reason}
        record.called_tools.add(tool.name)
        record.tool_call_count += 1
        return None

    return guardrail
