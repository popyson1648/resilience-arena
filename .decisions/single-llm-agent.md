# Decision

## Title

Use a single ADK LlmAgent instead of a multi-agent setup

## Date

2026-07-25

## Status

accepted

## Decision

Implement the incident responder as one `LlmAgent` with five function tools and a
`before_tool_callback` guardrail. Do not use sub-agents or ADK workflow agents.

## Context

Requirements section 9 allows any agent count but forbids multi-agent setups without technical
necessity, and section 26 excludes multi-agent designs that exist only for show. The MVP has one
scenario, five tools, and a serial investigate → recover → verify flow.

## Alternatives

- Multi-agent (investigator / operator / verifier) with separated permissions.
- ADK workflow agents (SequentialAgent) to force stage ordering.

## Reason

A single agent satisfies every requirement with less code and simpler debugging (requirements
section 23 priority 3). Stage ordering and permission limits are enforced deterministically by the
guardrail callback and server-side stage derivation, which is stronger than prompt-level separation.

## Consequences

Stage display cannot rely on agent hand-offs; the orchestrator derives stages from the event stream.

## Revisit Conditions

Revisit if additional scenarios need genuinely separated authority (e.g. an approval agent) or the
single instruction becomes unmanageable.

## Related

`.plans/resilience-arena-mvp.md`
