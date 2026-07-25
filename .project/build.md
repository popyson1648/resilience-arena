# Build

## Prerequisites

- Python 3.12+ (3.13 recommended)
- Node.js 24+ / npm 11+
- Gemini access via Vertex AI: gcloud ADC locally (`gcloud auth application-default login`) and
  `backend/.env` with `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_PROJECT=<project>`,
  `GOOGLE_CLOUD_LOCATION=global`; never commit `.env`

## Setup

```sh
python3 -m venv backend/.venv
backend/.venv/bin/pip install -e "backend[dev]"
npm --prefix frontend install
```

## Build

```sh
npm --prefix frontend run build   # outputs frontend/dist
```

## Run

```sh
# backend API (serves frontend/dist when it exists)
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

# frontend dev server (proxies /api to :8000)
npm --prefix frontend run dev
```

## Common Failures

- `ruff`/`pytest` not found: the verification commands expect `backend/.venv` to exist (see Setup).
- Frontend build type errors: run `npm --prefix frontend run typecheck` for details; `npm run build`
  itself does not typecheck.
