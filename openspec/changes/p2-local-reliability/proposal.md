## Why

P0–P2 product behavior works in tests and in a rebuilt stack, but a default `docker compose up` left `trip_sessions` missing (session create 500) while health stayed green. Host tools also miss the Compose database, and the composition root still uses a canned dialogue stub instead of structured LLM unavailability. Fix this local reliability gap before P3 catalog migrations make it worse.

## What Changes

Cross-cutting: **infra + backend + docs**. Not frontend feature work.

- Apply pending Alembic revisions as part of API boot (Compose `api` and documented local uvicorn) so product session routes do not depend on a manual migrate step.
- Keep `GET /health` as liveness if the database is up but schema is behind; do not treat “process up” as “schema ready.”
- When the schema is still missing (race, wrong database, migrate failed), session create MUST fail honestly — not an untyped 500 that pretends the product is ready.
- Wire the composition root so missing `LLM_API_KEY` uses structured `LlmUnavailable` (heuristic intent stays). Stop substituting `LocalDialogueStub` canned text as a successful dialogue complete.
- Document host `DATABASE_URL` / `.env` so local alembic and live-DB pytest hit the Compose PostGIS (`at`/`at`/`at`). Call out host port-5432 collisions. Do not invent Wandr env names.
- Mark P0/P1 `validation.md` proofs that already hold.

**Non-goals:** P3 catalog/ARQ/PostGIS places; cookie signing; defaulting the LangGraph checkpointer to Postgres; Paris chip dedup; remapping Compose `db` host port (keep `5432` as SSOT with CI); Wandr endpoints/DTOs/env; generate or explore routes.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `api-foundation`: API boot applies pending schema revisions before serving session create; readiness stays a DB ping, not a substitute for migrate.
- `fail-soft-boundaries`: Unconfigured LLM complete at the composition root is structured unavailable (not canned dialogue success); missing/unapplied schema is an honest failure, not a raw crash pretending readiness.
- `guest-chat-sessions`: Guest `POST /api/v1/sessions` succeeds after Compose API+DB start without a separate manual `alembic upgrade` (when the configured database is the product PostGIS).

## Impact

- `Dockerfile` / Compose `api` entry (or equivalent boot hook), `src/main.py` / settings, `src/modules/llm/litellm_adapter.py` (`build_llm_gateway`), possibly a small migrate helper
- `.env.example`, `README.md`, `system-docs/phase-slices/p0-foundation/validation.md`, `system-docs/phase-slices/p1-chat/validation.md`
- Tests: boot/migrate proof; session create against a freshly migrated DB; composition-root LLM unavailable (not stub string)
- No new public HTTP paths. No frontend contract change.
