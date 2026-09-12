# agentic-trip

Conversational trip OS. FastAPI modular monolith at `/src` plus a minimal Next.js chat shell in `frontend/`.

## Run the API locally

```bash
# Python 3.12 via uv
uv sync
cp .env.example .env   # set DATABASE_URL (must reach Compose PostGIS user/db `at`)
docker compose up -d db
# If alembic/pytest say role "at" does not exist, another Postgres owns host 5432 —
# stop that instance or point DATABASE_URL at the Compose published port.
uv run alembic upgrade head
# Or set APPLY_SCHEMA_ON_BOOT=true and: uv run python -m src.boot
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Probes:

- `GET /health` — liveness (process up)
- `GET /health/ready` — database ping

Chat + dialogue scope (P1–P2):

- `POST /api/v1/sessions` — create guest session (`Set-Cookie: at_guest`)
- `POST /api/v1/sessions/{id}/messages` — SSE dialogue (`token` / `message` / `error` / `hitl`)
- `GET /api/v1/sessions/{id}` — session projection (`hitl?`, `trip_scope?`)
- `POST /api/v1/sessions/{id}/hitl` — resume HITL (`choice_id` or `text`) → confirm `trip_scope`

Optional: set `LLM_API_KEY` for live LiteLLM; without keys complete is structured unavailable and heuristic intent stays honest. Set `DIALOGUE_PREFER_POSTGRES_CHECKPOINTER=true` to use a Postgres LangGraph checkpointer (session `hitl` remains the FE projection).

## Frontend chat shell

```bash
# terminal 1: API as above
# terminal 2:
cd frontend
npm install
NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
```

Open http://localhost:3000 — the page creates a guest session, streams replies, and shows **HITL chips** when place matches are ambiguous.

**Manual proof (P1):** send a trip prompt → see streamed reply (or clarification / honest error). No generate button.

**Manual proof (P2 HITL chips):** send e.g. `4 days in Paris` (ambiguous) → chips appear → pick a chip → same session continues and `trip_scope` is set (confirm via GET session / status line). No search-first-only path.

## Compose (API + PostGIS)

```bash
docker compose up --build
```

`db` is `postgis/postgis:16-3.x`. The API applies pending Alembic revisions on boot (`APPLY_SCHEMA_ON_BOOT`) — no separate host `alembic upgrade` is required for `POST /api/v1/sessions`. The API image does not require Redis. HITL is LangGraph interrupt + session projection — not an ARQ job.

`GET /health` is liveness (process up), not proof that schema is applied. `GET /health/ready` is a database ping, not a schema checksum.

## Tests

```bash
uv run alembic upgrade head   # when PostGIS is up
uv run pytest
```

CI runs `uv run pytest` (includes P2 geo/scope/dialogue/HITL/golden cases). Failures block merge.
