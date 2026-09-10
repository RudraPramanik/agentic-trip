# P0 Foundation — blueprint

> Status: planning blueprint (implement via later OpenSpec `p0-foundation`).

## Goal

Scaffold root modular monolith (`/src`), Docker API+PostGIS, health, **monitor** + **evals** module shells (fail-soft no-ops OK), empty feature module shells, guest AuthPort stub, LlmGateway stub.

## Scope / modules

- `src/main.py`, `core/`, `db/`, `ports/` stubs
- `modules/` shells: chat, geo, catalog, planner, trips, explore, media, booking, llm, agents, auth, **monitor**, **evals**
- `workers/` package placeholder (ARQ later)
- `alembic/`, `tests/` (+ `tests/evals` placeholder), `Dockerfile`, `docker-compose`
- `frontend/` stub optional

**Note:** Deep monitor/evals behavior can land later (per phase + P9); P0 only needs importable packages and fail-soft no-ops so tracing/eval hooks have a home.

## Step plan (high level)

1. Read this blueprint + guardrails + validation before coding.
2. OpenSpec propose/apply `p0-foundation` when starting implementation.
3. Implement behind ports/services; no vendor SDKs in routers.
4. Meet proof below; do not start the next slice until validation passes.

## Proof

`GET /health`; pytest smoke; CI workflow smoke (or documented local gate); monitor no-op without keys; evals smoke runner importable

## Explicit non-goals

- Do not pull work from later slices (no real chat/generate).
- Do not invent Wandr APIs or DTOs.
- Do not require Langfuse keys for health to pass.
