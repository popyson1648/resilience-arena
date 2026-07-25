# Decision

## Title

Single Cloud Run service with SSE streaming and in-memory run state

## Date

2026-07-25

## Status

accepted

## Decision

Deploy one Cloud Run service: FastAPI serves the API and the built Vite frontend. Agent progress is
streamed over Server-Sent Events (`text/event-stream`) from an in-memory run registry. No database.

## Context

Requirements section 22 allows one or two services, discourages unnecessary Google Cloud services,
and states persistence must not be added when the core experience does not need it. A demo run
completes in 30-60 seconds.

## Alternatives

- Separate frontend (CDN / second service) and backend services.
- WebSockets instead of SSE.
- Firestore/Redis for run state.

## Reason

One service removes CORS and deploy-order failure modes (section 23 priorities 1-3). SSE is
unidirectional, which matches the event flow, works with plain `EventSource`, and reconnects
automatically. In-memory state is acceptable because runs are short-lived; `--min-instances 1` and a
snapshot endpoint cover reconnects.

## Consequences

Runs are lost on instance restart; a reload falls back to the snapshot endpoint or a fresh run.
Multi-instance scaling is capped low so SSE and state stay on one instance.

## Revisit Conditions

Revisit if run history persistence becomes a submitted feature or traffic requires horizontal
scaling.

## Related

`.plans/resilience-arena-mvp.md`
