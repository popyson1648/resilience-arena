# Plan

## Status

done

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

- [x] Criterion 1: `python3 scripts/verify.py` passes with lint, format, typecheck, unit tests, and
      frontend build enabled. (Evidence: all phases green, final run 2026-07-25.)
- [x] Criterion 2: A demo run completes locally: fault injection → agent investigation via tools →
      rollback → health verification → recovered state, driven by runtime Gemini decisions.
      (Evidence: local Vertex run RECOVERED in 21.1s, 6 tool calls.)
- [x] Criterion 3: The single-screen UI (SmartHR UI) shows system state, agent activity, and result
      simultaneously; states are distinguishable without relying on color alone (icons + labels).
      (Evidence: Chrome E2E screenshots, a11y snapshot.)
- [x] Criterion 4: Wrong rollback targets do not lead to a success verdict; rollback without
      observed evidence is blocked and counted. (Evidence: pytest
      test_wrong_rollback_target_fails_run, test_premature_rollback_is_blocked_then_recovers.)
- [x] Criterion 5: The app runs on Cloud Run at a public URL without login; Gemini is called via
      Vertex AI with the service-account identity, no credentials reach the browser.
      (Evidence: https://resilience-arena-qxieomr5ba-an.a.run.app full-demo E2E, console clean.)

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

- Gemini via Vertex AI (`GOOGLE_GENAI_USE_VERTEXAI=TRUE`), ADC locally, service account on
  Cloud Run. (Changed from API key on 2026-07-25: the key path now requires manual AI Studio
  prepaid credits; user approved the switch. See `.decisions/vertex-ai-auth.md`.)
- Default model `gemini-3.5-flash`, overridable via `GEMINI_MODEL`.
- GCP project `resilience-arena-0725-15726`, billing linked with user approval (2026-07-25).

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

- [x] Phase 1: scaffold + simulation engine
- [x] Phase 2: ADK agent + API (real-Gemini smoke passed locally via Vertex on 2026-07-25)
- [x] Phase 3: frontend UI (verified in Chrome via scripted event source: full run, reset, re-run,
      error path, console clean)
- [x] Phase 4: integration + Cloud Run deploy (public URL live, full-demo E2E passed twice)

## Loop State

- Current cycle: 5 (complete)
- Last material observation: v3 (healthz path fix + favicon) live on Cloud Run; public-URL
  full-demo E2E passed (18.1s, RECOVERED) with zero console messages.
- Next action: none — task complete. Follow-ups: README/screenshots/slides deliverables,
  optional gitleaks secrets phase.
- Consecutive cycles without material progress: 0
- Stop or escalation reason: success

## Verification

- [x] `python3 scripts/verify.py`: lint, format, typecheck, test_unit (28 tests), build — all green
- [x] `cd backend && .venv/bin/python -m pytest`: engine determinism, wrong-rollback invariance,
      guardrails, orchestrator states, API/SSE
- [x] Phase 2: run snapshot API shows full state transitions and tool-call sequence (local Vertex
      run 1aae8498957d: RECOVERED, 21.1s)
- [x] Phase 3: Chrome DevTools MCP — screenshots (idle/running/final), a11y snapshot, console clean
- [x] Phase 4: public Cloud Run URL full demo twice (14.8s and 18.1s, RECOVERED), reset and re-run
      verified, no console messages, /api/healthz OK

## Open Issues

- styled-components v5 peerDeps may not declare React 19; resolve via npm `overrides` if needed and
  record the outcome in `.decisions/`.
