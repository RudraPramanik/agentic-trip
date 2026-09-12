## Context

See `proposal.md` for why. Current contracts: `openspec/specs/api-foundation`, `fail-soft-boundaries`, `guest-chat-sessions`, plus the deltas in this change.

Constraints that shape the approach:

- `create_app()` is used by ASGI unit tests that must not migrate a host Postgres (and must not require one).
- Compose `api` already injects `DATABASE_URL` to `db:5432`; the image CMD is `uv run --no-dev uvicorn …` and does not run Alembic.
- `alembic/env.py` already talks to `get_settings().database_url` (async). Revisions `0001`/`0002` are the current head.
- `parse_intent` already falls back to heuristics when complete returns structured unavailable. `build_llm_gateway(..., dialogue_stub_fallback=True)` is what violates the fail-soft contract at the composition root.
- Host `localhost:5432` may be a different Postgres than Compose `db` (role `at` missing). CI already sets `DATABASE_URL` to Compose-compatible credentials on `5432`.

## Goals / Non-Goals

**Goals:**

- One boot path that applies head revisions before the API accepts session traffic, without teaching unit tests to migrate.
- Honest HTTP problem body when the session table is still missing.
- Composition root matches existing fail-soft LLM contract; heuristic dialogue stays.
- Operators can point host alembic/pytest at Compose PostGIS without new env var names.

**Non-Goals:**

- Changing readiness to include a schema checksum (stays a ping).
- Remapping Compose `db` published port.
- Signing cookies, Postgres checkpointer default, or frontend HITL UX.

## Decisions

### 1. Apply schema in a Docker/local entrypoint, not inside every `create_app()`

`APPLY_SCHEMA_ON_BOOT` (default false in tests) gates a blocking `alembic upgrade head` **before** uvicorn binds. Compose `api` sets it true. Documented local `uvicorn` uses the same flag via `.env.example`.

- **Why not migrate inside `create_app()` / FastAPI lifespan by default:** TestClient builds the app dozens of times; a default migrate would hit whatever `DATABASE_URL` conftest injects (or the wrong host Postgres).
- **Why not a second Compose `migrate` service:** Extra service to forget; entrypoint-on-api is one process the operator already starts.
- **Why not only README “run alembic”:** That is the current failure mode.

Implementation shape: small shell/Python entry (`scripts/run-api` or `python -m src.boot`) — upgrade when the flag is set, then exec uvicorn. Dockerfile CMD switches to that entry. Idempotent upgrades are safe on restart.

### 2. Keep health/ready semantics; map missing-table to 503 + problem body

`GET /health` stays process-up. `GET /health/ready` stays DB ping.

Session create (and other SQL session writes) catch “relation does not exist” / equivalent and return **503** with a JSON body such as `{"detail":{"code":"schema_unavailable","message":"…"}}`. No new public path. Do not invent a session row or itinerary.

### 3. Composition root: `dialogue_stub_fallback=False`

`create_app()` wires `build_llm_gateway(api_key=..., dialogue_stub_fallback=False)` so unconfigured complete is `LlmUnavailable`. Keep `LocalDialogueStub` in-tree for explicit tests only.

- **Why not delete the stub:** Useful as a named test double; the defect is wiring it as the process gateway.
- **Why not require a live LLM key:** Violates P0 fail-soft and existing specs.

### 4. Host DX is documentation + existing `DATABASE_URL`, not a new port

Keep Compose `5432` (CI SSOT). `.env.example` already has `postgresql+asyncpg://at:at@localhost:5432/at`. README MUST say: copy to `.env`; if alembic/pytest report `role "at" does not exist`, another Postgres owns host `5432` — stop it or point `DATABASE_URL` at the Compose published port. No Wandr env names. No default port remap.

### 5. Dockerfile CMD should not rebuild the package on every start

`uv run` currently rebuilds on container start (slow empty replies). CMD/entrypoint SHOULD invoke the image venv uvicorn (or `uv run --no-sync`) after migrate so boot is migrate + bind, not a package rebuild.

## Risks / Trade-offs

- **[Risk] Boot migrate against the wrong host DB** → Mitigation: flag off in tests; Compose uses `db` hostname; README collision note.
- **[Risk] Two API replicas migrate concurrently** → Mitigation: v1 is one `api` replica; Alembic version table is the lock; P3 can revisit.
- **[Risk] Entrypoint migrate fails, container restarts in a loop** → Mitigation: fail boot with a clear log; health never claims ready schema; 503 if a request lands mid-failure.
- **[Risk] 503 vs 500 clients** → Mitigation: documented `schema_unavailable`; FE already surfaces create-session failure text.
- **[Trade-off] Ready stays ping-only** → Schema-behind + ping-ok still possible for a race window; liveness/ready stay as specified.

## Migration Plan

1. Ship entrypoint + Compose env flag + honest 503 + LLM wiring + docs/validation ticks.
2. Rebuild Compose `api`. Existing volumes: upgrade is incremental (`0002` no-op if already applied).
3. Rollback: revert image/CMD to uvicorn-only (manual alembic again) and restore `dialogue_stub_fallback=True` — no data migration to undo.
