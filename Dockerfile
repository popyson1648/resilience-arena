# Stage 1: build the frontend
FROM node:24-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: runtime
FROM python:3.13-slim
WORKDIR /srv
COPY backend/pyproject.toml backend/
COPY backend/app backend/app
RUN pip install --no-cache-dir ./backend && useradd -m app
COPY --from=frontend /build/dist frontend/dist
USER app
WORKDIR /srv/backend
# PORT is provided by Cloud Run; default to 8080 for local runs
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
