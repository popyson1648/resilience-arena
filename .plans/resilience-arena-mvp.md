# Plan

## Status

in-progress

## Date

2026-07-25

## Issues

None

## Goal

Build and deploy the Resilience Arena MVP: a fault-recovery simulator where an ADK + Gemini agent
investigates a simulated incident, performs a safe rollback, and verifies recovery, with the whole
process visualized in real time on a single screen. Source requirements: `.tmp/requirements.md`
(hackathon submission requirements, sections 1-30).

## Success Criteria

- [ ] Criterion 1: `python3 scripts/verify.py` passes with lint, format, typecheck, unit tests, and
      frontend build enabled.
- [ ] Criterion 2: A demo run completes locally: fault injection → agent investigation via tools →
      rollback → health verification → recovered state, driven by runtime Gemini decisions.
- [ ] Criterion 3: The single-screen UI (SmartHR UI) shows system state, agent activity, and result
      simultaneously; states are distinguishable without relying on color alone.
- [ ] Criterion 4: Wrong rollback targets do not lead to a success verdict; rollback without
      observed evidence is blocked and counted.
- [ ] Criterion 5: The app runs on Cloud Run at a public URL without login, with the API key kept
      server-side (Secret Manager).

## Scope

- Monorepo: `backend/` (FastAPI + google-adk 2.5.0, Python 3.13) and `frontend/` (React 19 + Vite +
  smarthr-ui 98).
- One fault scenario: bad deploy raises error rate; rollback to the previous revision recovers.
- Single Cloud Run service serving API + built static frontend; SSE streaming.
- Deployment to a newly created GCP project.

## Non-goals

- README/screenshots/presentation deliverables (follow-up task).
- Multiple scenarios, persistence, real Cloud Monitoring/Logging integration, multi-agent setups.

## Assumptions

- Gemini API key auth (`GOOGLE_API_KEY`, `GOOGLE_GENAI_USE_VERTEXAI=FALSE`); user supplies the key.
- Default model `gemini-3.5-flash`, overridable via `GEMINI_MODEL`.
- User links billing to the new GCP project and issues the API key (browser steps).

## Stop Conditions

- Success: all success criteria have evidence on the integrated state.
- No progress: two consecutive cycles without material progress.
- Limits: maximum 8 cycles per phase chunk.
- Other: approval boundary reached (billing, key issuance, deploy execution).

## Approval Boundaries

- Already-authorized actions (user-approved plan, 2026-07-25): local scaffolding and implementation,
  branch `feature/phase1-1-resilience-arena-mvp`, enabling verification phases, creating the GCP
  project and deploying to Cloud Run as Phase 4 within this task.
- Actions requiring confirmation: billing account link, Gemini API key issuance and handling,
  merge/PR, any action outside this repository or the new GCP project.

## Steps

- Phase 1: scaffold backend/frontend, update `.gitignore` / `.project/verification.toml` /
  `.github/workflows/ci.yml`, record decisions, implement deterministic simulation engine + pytest.
- Phase 2: ADK smoke test with a real key, then tools / guardrail callbacks / agent / orchestrator /
  API (SSE), tests with a scripted fake event source.
- Phase 3: single-screen frontend (5 areas), SSE client, custom SVG diagram + chart, error UI.
- Phase 4: Dockerfile, local container verification, GCP project setup, Cloud Run deploy, public E2E.

## Progress

- [~] Phase 1: scaffold + simulation engine
- [ ] Phase 2: ADK agent + API
- [ ] Phase 3: frontend UI
- [ ] Phase 4: integration + Cloud Run deploy

## Loop State

- Current cycle: 1 (Phase 1)
- Last material observation: plan approved; branch created; smarthr-ui 98.1.1 / google-adk 2.5.0
  facts verified against npm/PyPI/source.
- Next action: scaffold backend package and simulation engine with tests.
- Consecutive cycles without material progress: 0
- Stop or escalation reason: none

## Verification

- [ ] `python3 scripts/verify.py`: lint, format, typecheck, test_unit, build phases pass
- [ ] `cd backend && python3 -m pytest`: engine determinism, wrong-rollback invariance, guardrails
- [ ] Phase 2: `curl -N localhost:8000/api/runs/{id}/events` shows state transitions and tool calls
- [ ] Phase 3: Chrome DevTools MCP screenshot + console + network checks
- [ ] Phase 4: full demo on the public Cloud Run URL, repeated runs and reset

## Open Issues

- styled-components v5 peerDeps may not declare React 19; resolve via npm `overrides` if needed and
  record the outcome in `.decisions/`.
