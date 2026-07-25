import asyncio

from app.run.orchestrator import RunManager
from app.run.states import RunState, Stage
from app.simulation.scenario import APP

from .helpers import HAPPY_STEPS, scripted_run


def make_manager(steps):
    return RunManager(
        event_source_factory=lambda engine, record: scripted_run(engine, record, steps)
    )


async def finished_run(steps):
    manager = make_manager(steps)
    run = manager.create_run()
    await asyncio.wait_for(run.task, timeout=5)
    return run


def events_of(run, type_):
    return [e for e in run.history if e.type == type_]


async def test_happy_path_recovers():
    run = await finished_run(HAPPY_STEPS)
    assert run.state == RunState.RECOVERED
    result = events_of(run, "result")[0].payload
    assert result["success"] is True
    assert result["verified"] is True
    assert result["safety_blocked_count"] == 0
    assert result["tool_call_count"] == 6
    assert "rev-001" in result["recovery_action"]
    assert result["root_cause_summary"].startswith("原因:")


async def test_happy_path_stage_progression():
    run = await finished_run(HAPPY_STEPS)
    stages = [e.payload["stage"] for e in events_of(run, "stage")]
    assert stages == [
        Stage.SITUATION,
        Stage.PLANNING,
        Stage.SITUATION,  # check_health before recovery re-enters situation assessment
        Stage.METRICS,
        Stage.LOGS,
        Stage.DEPLOYS,
        Stage.CAUSE,
        Stage.RECOVERY,
        Stage.VERIFY,
        Stage.DONE,
    ]
    states = [e.payload["state"] for e in events_of(run, "run_state")]
    assert states == [
        RunState.FAULT_INJECTED,
        RunState.INVESTIGATING,
        RunState.CAUSE_IDENTIFIED,
        RunState.RECOVERING,
        RunState.VERIFYING,
        RunState.RECOVERED,
    ]


async def test_tool_call_carries_reason():
    run = await finished_run(HAPPY_STEPS)
    first_call = events_of(run, "tool_call")[0].payload
    assert first_call["tool"] == "check_health"
    assert "正常性" in first_call["reason"]


async def test_premature_rollback_is_blocked_then_recovers():
    steps = [
        ("text", "すぐにロールバックします。"),
        ("tool", "rollback_revision", {"service": APP, "target_revision": "rev-001"}),
        ("text", "根拠が不足しているため調査します。"),
        ("tool", "get_metrics", {"service": APP}),
        ("tool", "get_deploy_history", {"service": APP}),
        ("text", "rev-002 デプロイが原因です。"),
        ("tool", "rollback_revision", {"service": APP, "target_revision": "rev-001"}),
        ("tool", "check_health", {"service": "all"}),
        ("text", "原因: rev-002\n実施した操作: ロールバック\n検証結果: 正常"),
    ]
    run = await finished_run(steps)
    assert run.state == RunState.RECOVERED
    blocked = events_of(run, "safety_blocked")
    assert len(blocked) == 1
    assert "根拠" in blocked[0].payload["reason"]
    result = events_of(run, "result")[0].payload
    assert result["safety_blocked_count"] == 1
    assert result["success"] is True


async def test_missing_verification_fails_run():
    steps = [
        ("tool", "get_metrics", {"service": APP}),
        ("tool", "get_deploy_history", {"service": APP}),
        ("tool", "rollback_revision", {"service": APP, "target_revision": "rev-001"}),
        ("text", "復旧しました。"),
    ]
    run = await finished_run(steps)
    assert run.state == RunState.RECOVERY_FAILED
    result = events_of(run, "result")[0].payload
    assert result["success"] is False
    assert result["verified"] is False
    assert "検証" in result["verification_summary"]


async def test_wrong_rollback_target_fails_run():
    steps = [
        ("tool", "get_metrics", {"service": APP}),
        ("tool", "get_deploy_history", {"service": APP}),
        ("tool", "rollback_revision", {"service": APP, "target_revision": "rev-999"}),
        ("tool", "check_health", {"service": "all"}),
        ("text", "復旧を試みました。"),
    ]
    run = await finished_run(steps)
    assert run.state == RunState.RECOVERY_FAILED
    result = events_of(run, "result")[0].payload
    assert result["success"] is False
    assert result["recovery_action"] == "実行されず"


async def test_source_exception_becomes_execution_error():
    async def failing(engine, record):
        raise RuntimeError("boom")
        yield  # noqa: B901

    manager = RunManager(event_source_factory=failing)
    run = manager.create_run()
    await asyncio.wait_for(run.task, timeout=5)
    assert run.state == RunState.EXECUTION_ERROR
    errors = events_of(run, "error")
    assert errors
    assert "boom" not in errors[0].payload["message"]  # no internal details leak


async def test_system_state_transitions_to_recovered():
    run = await finished_run(HAPPY_STEPS)
    snapshots = [e.payload for e in events_of(run, "system_state")]
    assert snapshots[0]["phase"] == "faulted"
    assert snapshots[-1]["phase"] == "recovered"
