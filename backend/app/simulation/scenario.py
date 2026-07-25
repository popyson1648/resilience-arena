"""Scenario definition: a bad deploy raises the error rate until it is rolled back.

All times are simulation-clock minutes since 00:00. The scenario is pure data so the
engine stays deterministic and testable.
"""

from pydantic import BaseModel

APP = "checkout-app"
LB = "frontend-lb"
DB = "orders-db"
CLIENT = "client"

# Services the observation tools accept (the client is a traffic source, not observable).
OBSERVABLE_SERVICES = (LB, APP, DB)


class Baseline(BaseModel):
    requests_per_min: int
    error_rate_pct: float
    latency_p95_ms: int


class Scenario(BaseModel):
    id: str
    name: str
    description: str
    good_revision: str
    bad_revision: str
    deploy_minute: int  # bad revision goes live
    anomaly_start_minute: int  # metrics degrade from here
    initial_now_minute: int  # "now" when a run starts (fault already visible)
    rollback_recovery_minutes: int  # minutes until metrics normalize after rollback
    app_baseline: Baseline
    app_faulted: Baseline
    lb_baseline: Baseline
    lb_faulted: Baseline
    db_baseline: Baseline
    error_log_messages: list[str]
    lb_warning_message: str
    seed: str


BAD_DEPLOY = Scenario(
    id="bad-deploy",
    name="デプロイ起因のエラー率上昇",
    description=(
        "ECサイトの決済サービスで、新しいリビジョンの公開直後からエラー率が急上昇。"
        "AIエージェントが原因を調査し、安全な復旧操作を実行します。"
    ),
    good_revision="rev-001",
    bad_revision="rev-002",
    deploy_minute=10 * 60 + 31,  # 10:31
    anomaly_start_minute=10 * 60 + 32,  # 10:32
    initial_now_minute=10 * 60 + 41,  # 10:41
    rollback_recovery_minutes=2,
    app_baseline=Baseline(requests_per_min=850, error_rate_pct=0.4, latency_p95_ms=120),
    app_faulted=Baseline(requests_per_min=850, error_rate_pct=42.0, latency_p95_ms=480),
    lb_baseline=Baseline(requests_per_min=870, error_rate_pct=0.2, latency_p95_ms=95),
    lb_faulted=Baseline(requests_per_min=870, error_rate_pct=38.0, latency_p95_ms=430),
    db_baseline=Baseline(requests_per_min=1600, error_rate_pct=0.0, latency_p95_ms=8),
    error_log_messages=[
        "ConfigError: missing required config key PAYMENT_TIMEOUT",
        "Failed to initialize payment client: configuration invalid",
        "HTTP 500 returned for POST /api/checkout",
    ],
    lb_warning_message="upstream checkout-app returned 5xx",
    seed="resilience-arena-v1",
)
