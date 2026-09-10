# P0 Foundation — blueprint

> Status: planning blueprint (implement via later OpenSpec `p0-foundation`).

## Goal

Scaffold root modular monolith (`/src`), Docker API+PostGIS, health, obs/eval smoke, empty module shells, guest AuthPort stub, LlmGateway stub.

## Scope / modules

src/main.py, core, db, ports stubs, modules/* shells, obs, alembic, tests, Dockerfile, docker-compose, frontend stub optional

## Step plan (high level)

1. Read this blueprint + guardrails + validation before coding.
2. OpenSpec propose/apply `p0-foundation` when starting implementation.
3. Implement behind ports/services; no vendor SDKs in routers.
4. Meet proof below; do not start the next slice until validation passes.

## Proof

GET /health; pytest smoke; CI workflow smoke (or documented local gate); obs no-op without keys

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
