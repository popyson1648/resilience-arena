# Decision

## Title

Call Gemini through Vertex AI with ADC instead of an API key

## Date

2026-07-25

## Status

accepted

## Decision

Use the Vertex AI backend of ADK / google-genai: `GOOGLE_GENAI_USE_VERTEXAI=TRUE`,
`GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION=global`. Locally authenticate with the developer's
Application Default Credentials; on Cloud Run with the service's dedicated service account
(`roles/aiplatform.user`). No API key or Secret Manager entry exists.

## Context

The original plan used a Gemini API key. During Phase 4 the first real call returned
`429 RESOURCE_EXHAUSTED: Your prepayment credits are depleted` — the Gemini API key path now
requires prepaid credits purchased manually in AI Studio, which cannot be automated and adds a
second billing system. The user approved the switch (2026-07-25).

## Alternatives

- Buy AI Studio prepaid credits and keep the API key (manual browser step, separate billing).

## Reason

Vertex AI bills the already-linked Cloud Billing account pay-as-you-go, needs no manual purchase,
and removes the stored secret entirely — the Cloud Run identity is the credential.

## Consequences

Local development requires gcloud ADC. The unused API key and the `gemini-api-key` secret were
deleted. Model IDs stay the same.

## Revisit Conditions

Revisit if the project must run outside Google Cloud identities.

## Related

Supersedes [gemini-api-key-auth](gemini-api-key-auth.md). `.plans/resilience-arena-mvp.md`
