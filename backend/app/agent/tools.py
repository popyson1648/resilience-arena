"""Function tools bound to one run's simulation engine.

Tools are created per run via a factory so parallel runs never share state. ADK wraps
plain functions into FunctionTools using their names, signatures, and docstrings.
"""

from collections.abc import Callable

from app.simulation.engine import SimulationEngine

ALLOWED_TOOLS = frozenset(
    {"get_metrics", "search_logs", "get_deploy_history", "rollback_revision", "check_health"}
)

# Investigation evidence required before a rollback is allowed.
ROLLBACK_EVIDENCE_TOOLS = frozenset({"get_metrics", "get_deploy_history"})


def build_tools(engine: SimulationEngine) -> list[Callable]:
    def get_metrics(service: str, window_minutes: int = 30) -> dict:
        """指定サービスの時系列メトリクス(リクエスト数・エラー率・p95レイテンシ)を取得する。

        Args:
            service: 対象サービス名 (frontend-lb / checkout-app / orders-db)
            window_minutes: 現在時刻から遡る取得幅(分、5〜60)
        """
        return engine.get_metrics(service, window_minutes)

    def search_logs(service: str, window_minutes: int = 30, query: str = "") -> dict:
        """指定サービスのログを時間範囲と文字列条件で検索する。

        Args:
            service: 対象サービス名 (frontend-lb / checkout-app / orders-db)
            window_minutes: 現在時刻から遡る検索幅(分、5〜60)
            query: メッセージまたは重大度に対する部分一致フィルタ(空なら全件)
        """
        return engine.search_logs(service, window_minutes, query)

    def get_deploy_history(service: str) -> dict:
        """指定サービスのデプロイ履歴(現行/過去リビジョン、デプロイ時刻、ロールバック可否)を取得する。

        Args:
            service: 対象サービス名 (frontend-lb / checkout-app / orders-db)
        """
        return engine.get_deploy_history(service)

    def rollback_revision(service: str, target_revision: str) -> dict:
        """指定サービスのトラフィックを過去の安定リビジョンへ切り替える(復旧操作)。

        Args:
            service: 対象サービス名
            target_revision: 切り替え先のリビジョン名
        """
        return engine.rollback(service, target_revision)

    def check_health(service: str = "all") -> dict:
        """サービスの現在の正常性(ステータス・エラー率・レイテンシ)を確認する。

        Args:
            service: 対象サービス名、または "all" で全サービス
        """
        return engine.check_health(service)

    return [get_metrics, search_logs, get_deploy_history, rollback_revision, check_health]
