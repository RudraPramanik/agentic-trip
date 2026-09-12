# agentic-trip

Conversational trip OS. FastAPI modular monolith at `/src` plus a minimal Next.js chat shell in `frontend/`.

## Run the API locally

```bash
# Python 3.12 via uv
uv sync
cp .env.example .env   # set DATABASE_URL
docker compose up -d db
uv run alembic upgrade head
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Probes:

- `GET /health` — liveness (process up)
- `GET /health/ready` — database ping

Chat (P1):

- `POST /api/v1/sessions` — create guest session (`Set-Cookie: at_guest`)
- `POST /api/v1/sessions/{id}/messages` — SSE dialogue (`token` / `message` / `error`)
- `GET /api/v1/sessions/{id}` — session projection

## Frontend chat shell

```bash
# terminal 1: API as above
# terminal 2:
cd frontend
npm install
NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
```

Open http://localhost:3000 — the page creates a guest session, then send one message and watch streamed assistant text (local dialogue stub when no live LLM keys).

**Manual proof:** send a trip prompt → see streamed stub reply (or an honest SSE error if the LLM gateway is forced unavailable). No generate button in this shell.

## Compose (API + PostGIS)

```bash
docker compose up --build
```

`db` is `postgis/postgis:16-3.x`. The API image does not require Redis.

## Tests

```bash
uv run alembic upgrade head   # when PostGIS is up
uv run pytest
```
