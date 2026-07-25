"""Run states (requirements section 14) and agent stages (section 8)."""

from enum import StrEnum


class RunState(StrEnum):
    IDLE = "idle"
    FAULT_INJECTED = "fault_injected"
    INVESTIGATING = "investigating"
    CAUSE_IDENTIFIED = "cause_identified"
    RECOVERING = "recovering"
    VERIFYING = "verifying"
    RECOVERED = "recovered"
    RECOVERY_FAILED = "recovery_failed"
    EXECUTION_ERROR = "execution_error"


TERMINAL_STATES = {RunState.RECOVERED, RunState.RECOVERY_FAILED, RunState.EXECUTION_ERROR}


class Stage(StrEnum):
    SITUATION = "situation"  # 状況把握
    PLANNING = "planning"  # 調査計画
    METRICS = "metrics"  # メトリクス確認
    LOGS = "logs"  # ログ調査
    DEPLOYS = "deploys"  # デプロイ履歴確認
    CAUSE = "cause"  # 原因候補の決定
    RECOVERY = "recovery"  # 復旧操作の選択
    VERIFY = "verify"  # 復旧結果の検証
    DONE = "done"  # 終了判定


STAGE_LABELS: dict[Stage, str] = {
    Stage.SITUATION: "状況把握",
    Stage.PLANNING: "調査計画",
    Stage.METRICS: "メトリクス確認",
    Stage.LOGS: "ログ調査",
    Stage.DEPLOYS: "デプロイ履歴確認",
    Stage.CAUSE: "原因候補の決定",
    Stage.RECOVERY: "復旧操作の選択",
    Stage.VERIFY: "復旧結果の検証",
    Stage.DONE: "終了判定",
}
