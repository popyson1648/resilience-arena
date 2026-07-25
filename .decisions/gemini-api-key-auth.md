# Decision

## Title

Call Gemini with an API key instead of Vertex AI ADC

## Date

2026-07-25

## Status

superseded

## Decision

Use the Gemini API key backend (`GOOGLE_API_KEY` + `GOOGLE_GENAI_USE_VERTEXAI=FALSE`) through ADK /
google-genai. The key lives only server-side: `.env` locally (git-ignored) and Secret Manager on
Cloud Run.

## Context

ADK supports both the Gemini API and Vertex AI backends. The user chose the API key approach when
scoping the task (2026-07-25). Requirements section 12 forbids exposing credentials to the browser.

## Alternatives

- Vertex AI with Application Default Credentials on the Cloud Run service account.

## Reason

Identical code path for local development and Cloud Run, no ADC setup, fewer moving parts for a
hackathon deadline (requirements section 23 priority 1).

## Consequences

The key must be issued in Google AI Studio (manual browser step) and registered in Secret Manager.
Rate limits follow the AI Studio tier.

## Revisit Conditions

Revisit if the project moves to organization-managed GCP credentials or needs Vertex-only features.

## Related

Superseded by [vertex-ai-auth](vertex-ai-auth.md). `.plans/resilience-arena-mvp.md`
