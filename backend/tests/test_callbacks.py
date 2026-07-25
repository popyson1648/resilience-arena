from app.agent.callbacks import RunRecord, evaluate_tool_call


def test_unknown_tool_is_blocked():
    record = RunRecord()
    assert evaluate_tool_call(record, "run_shell") is not None


def test_rollback_without_evidence_is_blocked():
    record = RunRecord()
    reason = evaluate_tool_call(record, "rollback_revision")
    assert reason is not None
    assert "get_deploy_history" in reason
    assert "get_metrics" in reason


def test_rollback_with_partial_evidence_is_blocked():
    record = RunRecord(called_tools={"get_metrics"})
    reason = evaluate_tool_call(record, "rollback_revision")
    assert reason is not None
    assert "get_deploy_history" in reason


def test_rollback_with_full_evidence_is_allowed():
    record = RunRecord(called_tools={"get_metrics", "get_deploy_history"})
    assert evaluate_tool_call(record, "rollback_revision") is None


def test_observation_tools_always_allowed():
    record = RunRecord()
    for name in ["get_metrics", "search_logs", "get_deploy_history", "check_health"]:
        assert evaluate_tool_call(record, name) is None
