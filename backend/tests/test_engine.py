from app.simulation.engine import SimulationEngine, fmt_minute
from app.simulation.models import SystemPhase
from app.simulation.scenario import APP, BAD_DEPLOY, DB, LB


def faulted_engine() -> SimulationEngine:
    engine = SimulationEngine(BAD_DEPLOY)
    engine.inject_fault()
    return engine


def test_metrics_are_deterministic_across_runs():
    a = faulted_engine().get_metrics(APP, 30)
    b = faulted_engine().get_metrics(APP, 30)
    assert a == b


def test_healthy_before_fault_injection():
    engine = SimulationEngine(BAD_DEPLOY)
    health = engine.check_health()
    assert health["overall"] == "healthy"
    metrics = engine.get_metrics(APP, 30)
    assert metrics["summary"]["anomaly_started_at"] is None
    assert metrics["summary"]["current_error_rate_pct"] < 2.0


def test_fault_degrades_app_and_lb_but_not_db():
    engine = faulted_engine()
    health = engine.check_health()
    by_name = {s["name"]: s for s in health["services"]}
    assert health["overall"] == "down"
    assert by_name[APP]["status"] == "down"
    assert by_name[LB]["status"] == "warning"
    assert by_name[DB]["status"] == "healthy"
    assert by_name[DB]["error_rate_pct"] == 0.0


def test_anomaly_start_follows_deploy():
    engine = faulted_engine()
    metrics = engine.get_metrics(APP, 30)
    anomaly = metrics["summary"]["anomaly_started_at"]
    assert anomaly == fmt_minute(BAD_DEPLOY.anomaly_start_minute)
    deploys = engine.get_deploy_history(APP)
    bad = next(r for r in deploys["revisions"] if r["revision"] == BAD_DEPLOY.bad_revision)
    assert bad["deployed_at"] < anomaly  # deploy strictly precedes the anomaly


def test_error_logs_appear_only_after_anomaly_and_only_on_app():
    engine = faulted_engine()
    app_logs = engine.search_logs(APP, 60)
    errors = [e for e in app_logs["matched"] if e["severity"] == "ERROR"]
    assert errors
    anomaly = fmt_minute(BAD_DEPLOY.anomaly_start_minute)
    assert all(e["time"] >= anomaly for e in errors)
    assert any("ConfigError" in e["message"] for e in errors)
    db_logs = engine.search_logs(DB, 60)
    assert all(e["severity"] == "INFO" for e in db_logs["matched"])


def test_log_query_filters():
    engine = faulted_engine()
    result = engine.search_logs(APP, 30, query="configerror")
    assert result["total_matched"] > 0
    assert all("ConfigError" in e["message"] for e in result["matched"])


def test_wrong_rollback_targets_do_not_change_state():
    engine = faulted_engine()
    for service, revision in [
        (DB, BAD_DEPLOY.good_revision),  # service without revisions
        (APP, BAD_DEPLOY.bad_revision),  # already serving
        (APP, "rev-999"),  # unknown revision
        ("unknown-svc", BAD_DEPLOY.good_revision),
    ]:
        result = engine.rollback(service, revision)
        assert result["accepted"] is False, (service, revision)
        assert engine.phase == SystemPhase.FAULTED
        assert engine.check_health()["overall"] == "down"


def test_correct_rollback_recovers_the_system():
    engine = faulted_engine()
    result = engine.rollback(APP, BAD_DEPLOY.good_revision)
    assert result["accepted"] is True
    assert engine.phase == SystemPhase.RECOVERED
    health = engine.check_health()
    assert health["overall"] == "healthy"
    assert all(s["status"] == "healthy" for s in health["services"])
    metrics = engine.get_metrics(APP, 10)
    assert metrics["summary"]["current_error_rate_pct"] < 2.0
    deploys = engine.get_deploy_history(APP)
    assert deploys["current_revision"] == BAD_DEPLOY.good_revision


def test_unknown_service_returns_hint_instead_of_error():
    engine = faulted_engine()
    for result in [
        engine.get_metrics("nope"),
        engine.search_logs("nope"),
        engine.get_deploy_history("nope"),
        engine.check_health("nope"),
    ]:
        assert result["error"] == "unknown service"
        assert "known_services" in result


def test_snapshot_reflects_phase():
    engine = SimulationEngine(BAD_DEPLOY)
    assert engine.system_snapshot()["phase"] == "healthy"
    engine.inject_fault()
    snap = engine.system_snapshot()
    assert snap["phase"] == "faulted"
    statuses = {s["name"]: s["status"] for s in snap["services"]}
    assert statuses[APP] == "down"
    engine.rollback(APP, BAD_DEPLOY.good_revision)
    assert engine.system_snapshot()["phase"] == "recovered"
