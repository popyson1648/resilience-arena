import asyncio
import json

import httpx

from app.main import create_app
from app.run.orchestrator import RunManager

from .helpers import HAPPY_STEPS, scripted_run


def make_app():
    manager = RunManager(
        event_source_factory=lambda engine, record: scripted_run(engine, record, HAPPY_STEPS)
    )
    return create_app(run_manager=manager)


def client(app):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def test_scenario_endpoint_returns_healthy_initial_system():
    async with client(make_app()) as c:
        res = await c.get("/api/scenario")
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == "bad-deploy"
    assert body["initial_system"]["phase"] == "healthy"
    assert all(s["status"] == "healthy" for s in body["initial_system"]["services"])


async def test_run_lifecycle_snapshot_and_result():
    app = make_app()
    async with client(app) as c:
        created = await c.post("/api/runs")
        assert created.status_code == 201
        run_id = created.json()["run_id"]

        run = app.state.run_manager.get(run_id)
        await asyncio.wait_for(run.task, timeout=5)

        snapshot = (await c.get(f"/api/runs/{run_id}")).json()
        assert snapshot["state"] == "recovered"
        types = [e["type"] for e in snapshot["events"]]
        assert "tool_call" in types
        assert "result" in types


async def test_sse_stream_replays_history_and_completes():
    app = make_app()
    async with client(app) as c:
        run_id = (await c.post("/api/runs")).json()["run_id"]
        run = app.state.run_manager.get(run_id)
        await asyncio.wait_for(run.task, timeout=5)

        received = []
        async with c.stream("GET", f"/api/runs/{run_id}/events") as stream:
            async for line in stream.aiter_lines():
                if line.startswith("data: "):
                    received.append(json.loads(line[len("data: ") :]))
                if received and received[-1]["type"] == "system_state":
                    final_states = [e for e in received if e["type"] == "run_state"]
                    if any(e["payload"]["state"] == "recovered" for e in final_states):
                        break
        types = [e["type"] for e in received]
        assert types[0] == "run_state"
        assert "result" in types


async def test_unknown_run_returns_404():
    async with client(make_app()) as c:
        assert (await c.get("/api/runs/nope")).status_code == 404
        assert (await c.post("/api/runs/nope/cancel")).status_code == 404


async def test_cancel_marks_run_closed():
    app = make_app()
    async with client(app) as c:
        run_id = (await c.post("/api/runs")).json()["run_id"]
        res = await c.post(f"/api/runs/{run_id}/cancel")
        assert res.status_code == 200
        assert app.state.run_manager.get(run_id).closed is True
