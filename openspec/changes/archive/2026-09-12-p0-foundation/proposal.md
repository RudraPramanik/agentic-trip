## Why

The product bible, architecture, LLD, and phase-slices are settled, but this repo still has no `/src`. Later slices cannot implement chat, catalog, or generate until a modular monolith, health probes, ports, and fail-soft obs/evals shells exist. This is the first **code** change (`p0-foundation`), executed as P0.1–P0.12, one sub-phase proof at a time.

Work type: **backend + infra** (optional empty `frontend/` dir only). Not docs-only.

This change implements the product-goal P0 proof (health endpoint + empty shell) under the locked SWE call chain and fail-soft laws. It does not start the chat-first trip OS user journey; it only makes that journey implementable from P1.

## What Changes

- Scaffold the FastAPI modular monolith at repo root `/src` plus Compose `api` + PostGIS `db`, Alembic, pytest, and a CI smoke job.
- Add `GET /health` (liveness) and `GET /health/ready` (dependency probe). No `/api/v1/` product routes in this slice.
- Add Protocol/ABC port stubs and importable feature module shells, including `monitor` and `evals`.
- Ship fail-soft stubs: guest `AuthPort`, `LlmGateway` unavailable-without-keys, `ObsPort` no-op, workers package that does not require Redis to boot the API.
- Follow `system-docs/phase-slices/p0-foundation/` (blueprint, guardrails, validation), `system-docs/llm.md`, `system-docs/phase-slices/SHARED-SWE-LLD.md`, `system-docs/phase-slices/SHARED-FAIL-SOFT.md`, and `system-docs/product-goal.md`. P0 implements only this slice’s portion (boot fail-fast, health/ready, ports, obs/evals homes). Later-slice owners stay put (P1 cookie/session, P3 ARQ, P4 abort/timeout, P9 rate limits).

**Non-goals:** Wandr `guideagent` paths, DTOs, or env vars; chat/generate/HITL HTTP; Redis/ARQ jobs; Qdrant; Next.js UI; OAuth; live LiteLLM; invented coords/POIs/polylines; rate limits (P9); generate timeout (P4); unlocking last-trip Explore (requires a later authenticated `saved` trip).

**BREAKING:** none (no shipped product API yet).

## Capabilities

### New Capabilities

- `api-foundation`: Bootable modular monolith with health/ready probes, composition-root wiring of stubs, and importable feature/worker packages without requiring vendor keys or Redis.

### Modified Capabilities

- `fail-soft-boundaries`: Name boot-time fallbacks this slice actually ships — required env fail-fast, LLM gateway structured unavailable when unconfigured, DB down must not report ready, observability no-op (already required; P0 is the first implementation).

## Impact

- **Code / APIs:** new `src/` tree, `alembic/`, `tests/`, `GET /health`, `GET /health/ready`. No `/api/v1/sessions` or other later-slice routes. Routers stay HTTP-only (SWE call chain).
- **Infra:** `Dockerfile`, `docker-compose.yml` (`api` + PostGIS `db` only), CI smoke.
- **Docs:** implement against existing `system-docs/phase-slices/p0-foundation/` and `system-docs/llm.md`; if a blueprint method list and `llm.md` disagree, resolve both in this change (no third shape). Do not invent a twelfth product phase.
- **Deps:** FastAPI, uvicorn, pydantic-settings, SQLAlchemy asyncio, asyncpg, Alembic, pytest, structlog (as design). Langfuse/LiteLLM/Redis not required to pass P0.
