"""HTTP API. All endpoints are unauthenticated by design (public demo)."""

import asyncio
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.run.orchestrator import Run, RunManager
from app.simulation.engine import SimulationEngine
from app.simulation.scenario import BAD_DEPLOY

router = APIRouter(prefix="/api")

HEARTBEAT_SECONDS = 15


def _manager(request: Request) -> RunManager:
    return request.app.state.run_manager


@router.get("/scenario")
async def get_scenario() -> dict:
    """Scenario metadata plus the healthy pre-incident system for the idle screen."""
    healthy = SimulationEngine(BAD_DEPLOY).system_snapshot()
    return {
        "id": BAD_DEPLOY.id,
        "name": BAD_DEPLOY.name,
        "description": BAD_DEPLOY.description,
        "initial_system": healthy,
    }


@router.post("/runs", status_code=201)
async def create_run(request: Request) -> dict:
    """Async on purpose: RunManager.create_run schedules the agent task on this loop."""
    run = _manager(request).create_run()
    return {"run_id": run.id}


def _get_run(request: Request, run_id: str) -> Run:
    run = _manager(request).get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return run


@router.get("/runs/{run_id}")
async def get_run_snapshot(request: Request, run_id: str) -> dict:
    run = _get_run(request, run_id)
    return {
        "run_id": run.id,
        "state": run.state.value,
        "events": [e.model_dump() for e in run.history],
    }


@router.post("/runs/{run_id}/cancel")
async def cancel_run(request: Request, run_id: str) -> dict:
    _get_run(request, run_id)
    _manager(request).cancel(run_id)
    return {"cancelled": True}


@router.get("/runs/{run_id}/events")
async def stream_run_events(request: Request, run_id: str) -> StreamingResponse:
    run = _get_run(request, run_id)

    async def generate():
        history, queue = run.subscribe()
        try:
            for event in history:
                yield f"data: {json.dumps(event.model_dump(), ensure_ascii=False)}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
                except TimeoutError:
                    yield ": ping\n\n"
                    continue
                if event is None:
                    break
                yield f"data: {json.dumps(event.model_dump(), ensure_ascii=False)}\n\n"
        finally:
            if queue in run.subscribers:
                run.subscribers.remove(queue)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
