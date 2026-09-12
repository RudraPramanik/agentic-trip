# agentic-trip

Conversational trip OS. This repository is the FastAPI modular monolith at `/src` plus an optional `frontend/` stub.

## Run the API locally

```bash
# Python 3.12 via uv
uv sync
cp .env.example .env   # set DATABASE_URL
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Probes:

- `GET /health` — liveness (process up)
- `GET /health/ready` — database ping

## Compose (API + PostGIS)

```bash
docker compose up --build
```

`db` is `postgis/postgis:16-3.x`. The API image does not require Redis.

## Tests

```bash
uv run pytest
```
