"""Deterministic simulation engine for one incident run.

Every run gets its own engine instance. All series are generated as pure functions of
(scenario, minute) with a string-seeded PRNG, so repeated runs produce identical data.
Only `rollback` mutates state, and only the correct target transitions the system to
RECOVERED.
"""

import random

from .models import LogEntry, MetricPoint, Revision, ServiceInfo, ServiceStatus, SystemPhase
from .scenario import APP, CLIENT, DB, LB, OBSERVABLE_SERVICES, Baseline, Scenario


def fmt_minute(minute: int) -> str:
    return f"{minute // 60:02d}:{minute % 60:02d}"


class SimulationEngine:
    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario
        self.phase = SystemPhase.HEALTHY
        self.now = scenario.deploy_minute - 1
        self.rollback_minute: int | None = None
        self.current_revision = scenario.good_revision

    # -- lifecycle ---------------------------------------------------------

    def inject_fault(self) -> None:
        """Start the incident: the bad revision is live and 'now' is past the anomaly."""
        self.phase = SystemPhase.FAULTED
        self.current_revision = self.scenario.bad_revision
        self.now = self.scenario.initial_now_minute

    # -- internal helpers --------------------------------------------------

    def _rng(self, *key: object) -> random.Random:
        return random.Random(":".join([self.scenario.seed, *map(str, key)]))

    def _recovery_effective_minute(self) -> int | None:
        if self.rollback_minute is None:
            return None
        return self.rollback_minute + self.scenario.rollback_recovery_minutes

    def _levels_at(self, service: str, minute: int) -> Baseline:
        s = self.scenario
        if service == DB:
            return s.db_baseline
        baseline, faulted = (
            (s.app_baseline, s.app_faulted) if service == APP else (s.lb_baseline, s.lb_faulted)
        )
        if self.phase == SystemPhase.HEALTHY or minute < s.anomaly_start_minute:
            return baseline
        recovery = self._recovery_effective_minute()
        if recovery is not None and minute >= recovery:
            return baseline
        if recovery is not None and minute >= self.rollback_minute:  # decaying window
            frac = (recovery - minute) / s.rollback_recovery_minutes
            return Baseline(
                requests_per_min=baseline.requests_per_min,
                error_rate_pct=round(
                    baseline.error_rate_pct
                    + (faulted.error_rate_pct - baseline.error_rate_pct) * frac,
                    1,
                ),
                latency_p95_ms=int(
                    baseline.latency_p95_ms
                    + (faulted.latency_p95_ms - baseline.latency_p95_ms) * frac
                ),
            )
        return faulted

    def _point(self, service: str, minute: int) -> MetricPoint:
        levels = self._levels_at(service, minute)
        rng = self._rng("metrics", service, minute)
        return MetricPoint(
            time=fmt_minute(minute),
            requests_per_min=levels.requests_per_min + rng.randint(-25, 25),
            error_rate_pct=round(max(0.0, levels.error_rate_pct * rng.uniform(0.9, 1.1)), 1),
            latency_p95_ms=int(levels.latency_p95_ms * rng.uniform(0.92, 1.08)),
        )

    def _status_of(self, service: str) -> ServiceStatus:
        if service in (CLIENT, DB):
            return "healthy"
        recovery = self._recovery_effective_minute()
        degraded = self.phase == SystemPhase.FAULTED and (recovery is None or self.now < recovery)
        if not degraded:
            return "healthy"
        return "down" if service == APP else "warning"

    # -- observation tools -------------------------------------------------

    def get_metrics(self, service: str, window_minutes: int = 30) -> dict:
        if service not in OBSERVABLE_SERVICES:
            return {"error": "unknown service", "known_services": list(OBSERVABLE_SERVICES)}
        window_minutes = max(5, min(60, window_minutes))
        start = self.now - window_minutes + 1
        points = [self._point(service, m) for m in range(start, self.now + 1)]

        anomaly_started_at = None
        if service != DB and self.phase != SystemPhase.HEALTHY:
            anomaly = self.scenario.anomaly_start_minute
            if start <= anomaly <= self.now:
                anomaly_started_at = fmt_minute(anomaly)

        baseline = (
            self.scenario.db_baseline
            if service == DB
            else (self.scenario.app_baseline if service == APP else self.scenario.lb_baseline)
        )
        return {
            "service": service,
            "window_minutes": window_minutes,
            "points": [p.model_dump() for p in points],
            "summary": {
                "current_error_rate_pct": points[-1].error_rate_pct,
                "baseline_error_rate_pct": baseline.error_rate_pct,
                "anomaly_started_at": anomaly_started_at,
            },
        }

    def search_logs(self, service: str, window_minutes: int = 30, query: str = "") -> dict:
        if service not in OBSERVABLE_SERVICES:
            return {"error": "unknown service", "known_services": list(OBSERVABLE_SERVICES)}
        window_minutes = max(5, min(60, window_minutes))
        start = self.now - window_minutes + 1
        entries: list[LogEntry] = []
        for minute in range(start, self.now + 1):
            entries.extend(self._logs_at(service, minute))
        if query:
            q = query.lower()
            entries = [e for e in entries if q in e.message.lower() or q in e.severity.lower()]
        return {
            "service": service,
            "window_minutes": window_minutes,
            "total_matched": len(entries),
            "matched": [e.model_dump() for e in entries[-40:]],
        }

    def _logs_at(self, service: str, minute: int) -> list[LogEntry]:
        s = self.scenario
        time = fmt_minute(minute)
        levels = self._levels_at(service, minute)
        erroring = service != DB and levels.error_rate_pct > 5.0
        rng = self._rng("logs", service, minute)
        entries: list[LogEntry] = []
        if service == APP:
            entries.append(
                LogEntry(
                    time=time,
                    severity="INFO",
                    message=f"handled {levels.requests_per_min + rng.randint(-25, 25)} requests",
                )
            )
            if erroring:
                for msg in s.error_log_messages:
                    entries.append(LogEntry(time=time, severity="ERROR", message=msg))
        elif service == LB:
            entries.append(LogEntry(time=time, severity="INFO", message="health probes passing"))
            if erroring:
                entries.append(
                    LogEntry(time=time, severity="WARNING", message=s.lb_warning_message)
                )
        else:  # DB stays quiet and healthy
            entries.append(
                LogEntry(
                    time=time,
                    severity="INFO",
                    message=f"connections active: {40 + rng.randint(-5, 5)}, slow queries: 0",
                )
            )
        return entries

    def get_deploy_history(self, service: str) -> dict:
        if service not in OBSERVABLE_SERVICES:
            return {"error": "unknown service", "known_services": list(OBSERVABLE_SERVICES)}
        if service != APP:
            return {
                "service": service,
                "current_revision": None,
                "previous_revision": None,
                "revisions": [],
                "note": "this service is not deployed via revisions",
            }
        s = self.scenario
        rolled_back = self.current_revision == s.good_revision
        revisions = [
            Revision(
                revision=s.bad_revision,
                deployed_at=fmt_minute(s.deploy_minute),
                status="retired" if rolled_back else "serving",
                traffic_pct=0 if rolled_back else 100,
                stable=False,
                rollback_available=not rolled_back,
            ),
            Revision(
                revision=s.good_revision,
                deployed_at=fmt_minute(s.deploy_minute - 3 * 24 * 60),
                status="serving" if rolled_back else "retired",
                traffic_pct=100 if rolled_back else 0,
                stable=True,
                rollback_available=False,
            ),
        ]
        return {
            "service": service,
            "current_revision": self.current_revision,
            "previous_revision": s.good_revision if not rolled_back else None,
            "revisions": [r.model_dump() for r in revisions],
        }

    # -- recovery ----------------------------------------------------------

    def rollback(self, service: str, target_revision: str) -> dict:
        s = self.scenario
        if service != APP:
            return {
                "accepted": False,
                "service": service,
                "reason": f"service '{service}' has no revisions to roll back",
            }
        if target_revision == self.current_revision:
            return {
                "accepted": False,
                "service": service,
                "reason": f"'{target_revision}' is already the serving revision",
            }
        if target_revision != s.good_revision:
            return {
                "accepted": False,
                "service": service,
                "reason": f"unknown revision '{target_revision}'",
            }
        from_revision = self.current_revision
        self.current_revision = s.good_revision
        self.rollback_minute = self.now
        self.now += s.rollback_recovery_minutes + 1
        self.phase = SystemPhase.RECOVERED
        return {
            "accepted": True,
            "service": service,
            "from_revision": from_revision,
            "to_revision": s.good_revision,
            "message": (
                f"traffic switched to {s.good_revision} at {fmt_minute(self.rollback_minute)}"
            ),
        }

    def check_health(self, service: str = "all") -> dict:
        names = list(OBSERVABLE_SERVICES) if service == "all" else [service]
        unknown = [n for n in names if n not in OBSERVABLE_SERVICES]
        if unknown:
            return {"error": "unknown service", "known_services": [*OBSERVABLE_SERVICES, "all"]}
        services = []
        for name in names:
            point = self._point(name, self.now)
            services.append(
                {
                    "name": name,
                    "status": self._status_of(name),
                    "error_rate_pct": point.error_rate_pct,
                    "latency_p95_ms": point.latency_p95_ms,
                }
            )
        statuses = {s["status"] for s in services}
        overall = (
            "down" if "down" in statuses else "degraded" if "warning" in statuses else "healthy"
        )
        return {"overall": overall, "checked_at": fmt_minute(self.now), "services": services}

    # -- UI snapshot -------------------------------------------------------

    def system_snapshot(self) -> dict:
        services = [
            ServiceInfo(name=CLIENT, kind="client", label="利用者", status="healthy"),
            ServiceInfo(
                name=LB, kind="load_balancer", label="ロードバランサ", status=self._status_of(LB)
            ),
            ServiceInfo(
                name=APP, kind="application", label="決済サービス", status=self._status_of(APP)
            ),
            ServiceInfo(name=DB, kind="database", label="注文データベース", status="healthy"),
        ]
        app_metrics = self.get_metrics(APP, window_minutes=30)
        return {
            "phase": self.phase.value,
            "now": fmt_minute(self.now),
            "current_revision": self.current_revision,
            "services": [s.model_dump() for s in services],
            "app_metrics": app_metrics,
            "deploy_marker": fmt_minute(self.scenario.deploy_minute),
        }
