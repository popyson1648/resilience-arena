"""FastAPI application: API routes plus the built frontend as static files."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import FRONTEND_DIST
from app.run.orchestrator import RunManager


def create_app(run_manager: RunManager | None = None) -> FastAPI:
    app = FastAPI(title="Resilience Arena", docs_url=None, redoc_url=None)
    app.state.run_manager = run_manager or RunManager()
    app.include_router(router)

    @app.get("/healthz")
    def healthz() -> dict:
        return {"ok": True}

    dist = Path(__file__).resolve().parent.parent / FRONTEND_DIST
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return app


app = create_app()
