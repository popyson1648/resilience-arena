# Structure

## Top-level Directories

- `backend/` — FastAPI + google-adk service (Python). `app/` is the package, `tests/` is pytest.
- `frontend/` — React 19 + Vite + smarthr-ui single-page UI (TypeScript).
- `.plans/`, `.decisions/`, `.project/`, `.template/`, `scripts/` — process and verification files.

## Important Modules

- `backend/app/simulation/` — deterministic incident simulation: `scenario.py` (pure data),
  `engine.py` (state + generated metrics/logs/deploys), `models.py` (Pydantic models).
- `backend/app/agent/` — ADK agent, function tools, guardrail callbacks.
- `backend/app/run/` — run lifecycle: orchestrator (ADK events → SSE), run states, event schemas.
- `backend/app/api/` — HTTP routes (`/api/runs...`).
- `frontend/src/` — `App.tsx` layout, `api/` (SSE client + event types), `components/`.

## Where To Make Changes

- New fault scenarios: add data to `backend/app/simulation/scenario.py`; keep `engine.py` generic.
- Tool behavior: `backend/app/agent/tools.py`; safety rules: `backend/app/agent/callbacks.py`.
- SSE event shapes: change `backend/app/run/events.py` and mirror in `frontend/src/api/events.ts`.

## Areas That Require Extra Care

- `engine.py` must stay deterministic (string-seeded PRNG only; no wall-clock time).
- The final success verdict must come from engine state, never from model text.
- Never send internal error details or credentials to the browser.
