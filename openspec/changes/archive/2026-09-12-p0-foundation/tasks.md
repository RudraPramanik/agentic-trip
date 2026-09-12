## 1. Packaging and Compose (P0.1)

- [x] 1.1 infra: Add `pyproject.toml` (Python 3.12, uv, FastAPI, uvicorn, pydantic-settings) and make `src` an installable package
- [x] 1.2 infra: Add `Dockerfile` and `docker-compose.yml` with `api` + PostGIS `db` (`postgis/postgis:16-3.x`), no Redis/Qdrant
- [x] 1.3 docs: Add a short README run path (`uv run uvicorn src.main:app`) that does not mention Wandr

## 2. Settings and logging (P0.2)

- [x] 2.1 backend: Implement `src/core/settings.py` with required `DATABASE_URL` fail-fast and optional obs/LLM keys (do not default secrets to empty-and-configured)
- [x] 2.2 backend: Implement `src/core/logging.py` (`configure_logging` / structlog)
- [x] 2.3 backend: Unit test: missing `DATABASE_URL` raises a clear error; missing Langfuse keys do not

## 3. Database session and Alembic (P0.3)

- [x] 3.1 backend: Implement async engine/session (`pool_pre_ping=True`) and a `ping_db()` helper in `src/db/` (no place/trip queries)
- [x] 3.2 backend: Add Alembic baseline at repo root (no place/trip tables)
- [x] 3.3 backend: Proof: session factory importable; Alembic env points at metadata

## 4. Ports and feature shells (P0.4–P0.5)

- [x] 4.1 backend: Add `src/ports/` Protocols: `LlmGateway` (`complete`, `embed`), `AuthPort`, `ObsPort`, `GeoGateway`, `GenerateRunner`, `TravelEngine`, `PlaceRepository` (abstract / `NotImplementedError`; no vendor types)
- [x] 4.2 backend: Add empty importable `src/modules/{chat,geo,catalog,planner,trips,explore,media,booking,llm,agents,auth,monitor,evals}`
- [x] 4.3 backend: Tests: ports import with no side effects; every feature module imports with no network I/O
- [x] 4.4 docs: Align P0.4 method list in `system-docs/phase-slices/p0-foundation/blueprint.md` with `llm.md` (`embed` on `LlmGateway`); do not invent a third shape

## 5. Fail-soft stubs (P0.6–P0.8)

- [x] 5.1 backend: `StubAuthAdapter` issue/read guest id; cookie name `at_guest` (httpOnly, SameSite=Lax; not `wandr_session`)
- [x] 5.2 backend: `StubLlmGateway.complete` (and stub `embed`) returns structured `LlmUnavailable` without keys; import does not raise
- [x] 5.3 backend: `NoOpObs` no-op traces/spans/generations without Langfuse keys
- [x] 5.4 backend: Unit tests for 5.1–5.3 (including span without keys does not raise)

## 6. Evals smoke (P0.9)

- [x] 6.1 backend: `EvalRunner.run_smoke()` in `src/modules/evals/` plus `tests/evals/` collection
- [x] 6.2 backend: Proof: evals tests collect; runner importable (no golden trips)

## 7. Health API and composition root (P0.10)

- [x] 7.1 backend: `create_app()` in `src/main.py` wires stubs; `src/api/health.py` only parses HTTP; ready uses `ping_db` via `Depends` (no SQL in the router, no vendor SDKs)
- [x] 7.2 backend: `GET /health` → 200 `{ "status": "ok" }` even if DB/keys missing (liveness does not ping DB)
- [x] 7.3 backend: `GET /health/ready` → 200 `{ "status": "ok", "db": true }` or 503 `{ "status": "degraded", "db": false }`
- [x] 7.4 backend: ASGI tests for 7.2–7.3 (DB up and DB down)

## 8. Workers placeholder (P0.11)

- [x] 8.1 backend: Add importable `src/workers/` with no ARQ jobs
- [x] 8.2 backend: Proof: API tests pass with Redis absent

## 9. CI and slice proof (P0.12)

- [x] 9.1 infra: GitHub Actions job: uv + pytest; PostGIS service for ready tests; no Redis
- [x] 9.2 frontend: Optional `frontend/.gitkeep` only (no Next.js app)
- [x] 9.3 backend: `uv run pytest` green locally; ASGI proof that `POST /api/v1/sessions` and generate are not successful product routes; no Wandr `guideagent` paths
