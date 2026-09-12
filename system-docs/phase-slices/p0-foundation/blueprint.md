# P0 Foundation — blueprint

> Status: planning blueprint (implement via later OpenSpec `p0-foundation`).  
> LLD: [`../../llm.md`](../../llm.md)

## Goal

Scaffold root modular monolith (`/src`), Docker API+PostGIS, health, **monitor** + **evals** module shells (fail-soft no-ops OK), empty feature module shells, guest AuthPort stub, LlmGateway stub.

## Scope / modules

- `src/main.py`, `core/`, `db/`, `ports/` stubs
- `modules/` shells: chat, geo, catalog, planner, trips, explore, media, booking, llm, agents, auth, **monitor**, **evals**
- `workers/` package placeholder (ARQ later)
- `alembic/`, `tests/` (+ `tests/evals` placeholder), `Dockerfile`, `docker-compose`
- `frontend/` stub optional

**Note:** Deep monitor/evals behavior can land later (per phase + P9); P0 only needs importable packages and fail-soft no-ops so tracing/eval hooks have a home.

## Step plan

Implement **one sub-phase at a time**. Do not start P0.{m+1} until P0.{m} proof passes.

### P0.1 — Repo skeleton

- **Goal:** Create the installable API package and Compose files for `api` + PostGIS `db`.
- **Modules:** repo root (`pyproject.toml`, `src/`, `Dockerfile`, `docker-compose.yml`)
- **Types:** — (packaging only)
- **Functions:** — (no app functions yet)
- **Services:** none
- **Routes / APIs:** none
- **Algorithms / data:** — 
- **Depends on:** —
- **Proof:** `src` is a package; Compose file declares `api` and `db` (PostGIS image); `pyproject.toml` lists FastAPI/uvicorn/pydantic-settings
- **Non-goals:** Redis/worker/Qdrant; Next.js app; real routers

### P0.2 — Settings + logging

- **Goal:** Fail-fast settings and structured logging.
- **Modules:** `src/core/settings.py`, `src/core/logging.py`
- **Types:** `Settings` (pydantic-settings)
- **Functions:** `get_settings()`, `configure_logging()`
- **Services:** none
- **Routes / APIs:** none
- **Algorithms / data:** fail-fast on missing required env at boot
- **Depends on:** P0.1
- **Proof:** importing `get_settings` with incomplete env raises a clear error in a unit test; logging config importable
- **Non-goals:** vendor API keys required for health (Langfuse optional)

### P0.3 — DB session + Alembic

- **Goal:** Async engine/session and empty Alembic baseline.
- **Modules:** `src/db/session.py`, `src/db/base.py`, `alembic/`
- **Types:** SQLAlchemy `AsyncSession` factory
- **Functions:** `get_engine()`, `get_sessionmaker()`, `get_session()` (async generator)
- **Services:** none
- **Routes / APIs:** none
- **Algorithms / data:** connection pool via SQLAlchemy; no business queries
- **Depends on:** P0.2
- **Proof:** Alembic env points at metadata; session factory importable; compose `db` reachable from documented local command
- **Non-goals:** Place/trip tables (P3/P4)

### P0.4 — Ports package

- **Goal:** Protocol/ABC stubs for all gateways used later.
- **Modules:** `src/ports/` (or `src/modules/*/ports.py` re-exported)
- **Types:** `LlmGateway`, `AuthPort`, `ObsPort`, `GeoGateway`, `GenerateRunner`, `TravelEngine`, `PlaceRepository`
- **Functions:** abstract methods only: `complete`, `embed`, `issue_guest`, `start_trace`, `search`, `start`, `pack`, `retrieve`
- **Services:** none
- **Routes / APIs:** none
- **Algorithms / data:** —
- **Depends on:** P0.1
- **Proof:** ports import without side effects; methods are abstract or `NotImplementedError`
- **Non-goals:** LiteLLM/Nominatim implementations

### P0.5 — Feature module shells

- **Goal:** Importable empty feature packages.
- **Modules:** `src/modules/{chat,geo,catalog,planner,trips,explore,media,booking,llm,agents,auth,monitor,evals}/__init__.py`
- **Types:** — (packages)
- **Functions:** — 
- **Services:** none (shells only)
- **Routes / APIs:** none
- **Algorithms / data:** —
- **Depends on:** P0.1
- **Proof:** `import src.modules.<name>` for every module with no network I/O
- **Non-goals:** real ChatService / graphs

### P0.6 — Guest AuthPort stub

- **Goal:** Cookie-shaped guest identity without OAuth.
- **Modules:** `src/modules/auth/`
- **Types:** `GuestPrincipal`, `StubAuthAdapter(AuthPort)`
- **Functions:** `issue_guest()`, `read_principal()`
- **Services:** none (port only)
- **Routes / APIs:** none
- **Algorithms / data:** random/uuid guest id; httpOnly cookie name documented in LLD (not Wandr names)
- **Depends on:** P0.4
- **Proof:** unit test: issue + read round-trip on a fake request/response
- **Non-goals:** OAuth; durable user table

### P0.7 — LlmGateway stub

- **Goal:** Structured unavailable when keys missing; no crash on import.
- **Modules:** `src/modules/llm/`
- **Types:** `StubLlmGateway`, `LlmUnavailable`
- **Functions:** `complete(role, messages, schema=None)` returns typed unavailable
- **Services:** none
- **Routes / APIs:** none
- **Algorithms / data:** —
- **Depends on:** P0.4
- **Proof:** import + `complete("dialogue", ...)` without keys returns error object, does not raise
- **Non-goals:** LiteLLM live calls

### P0.8 — Monitor no-op

- **Goal:** `ObsPort` no-op tracer when Langfuse unconfigured.
- **Modules:** `src/modules/monitor/`
- **Types:** `NoOpObs`, `ObsPort`
- **Functions:** `start_trace()`, `span()`, `generation()` as no-ops
- **Services:** none
- **Routes / APIs:** none
- **Algorithms / data:** —
- **Depends on:** P0.4
- **Proof:** unit test: missing keys → no-op; calling span does not raise
- **Non-goals:** real Langfuse export (later phases)

### P0.9 — Evals smoke

- **Goal:** Importable golden runner shell.
- **Modules:** `src/modules/evals/`, `tests/evals/`
- **Types:** `EvalRunner` (smoke)
- **Functions:** `run_smoke()` (e.g. asserts health import)
- **Services:** none
- **Routes / APIs:** none
- **Algorithms / data:** —
- **Depends on:** P0.5
- **Proof:** `tests/evals` collects; runner importable
- **Non-goals:** Meghalaya/Japan goldens (P2/P4)

### P0.10 — Health API + app entry

- **Goal:** FastAPI app with health probes.
- **Modules:** `src/main.py`, `src/api/health.py`
- **Types:** `HealthResponse`, `ReadyResponse` (Pydantic)
- **Functions:** `health()`, `ready()`; `create_app()`
- **Services:** readiness checks DB via session (not a feature service)
- **Routes / APIs:** `GET /health`, `GET /health/ready`
- **Algorithms / data:** ready = db ping; unhealthy db → ready degraded/fail, health still liveness
- **Depends on:** P0.2, P0.3
- **Proof:** ASGI test `GET /health` 200; `GET /health/ready` reflects DB
- **Non-goals:** `/api/v1/sessions`

### P0.11 — Workers placeholder

- **Goal:** `workers/` package exists; ARQ not required to boot API.
- **Modules:** `src/workers/__init__.py`
- **Types:** —
- **Functions:** —
- **Services:** none
- **Routes / APIs:** none
- **Algorithms / data:** —
- **Depends on:** P0.5
- **Proof:** package importable; API tests pass without Redis
- **Non-goals:** `acquire_catalog` job (P3)

### P0.12 — Pytest + CI smoke

- **Goal:** Health pytest + module import tests + documented CI job.
- **Modules:** `tests/`, `.github/workflows/` or documented script
- **Types:** —
- **Functions:** test functions for health, imports, obs no-op
- **Services:** none
- **Routes / APIs:** exercise `GET /health`
- **Algorithms / data:** —
- **Depends on:** P0.8, P0.10
- **Proof:** pytest green locally; CI workflow or README script runs the same checks; optional `frontend/` stub dir only
- **Non-goals:** Next.js feature UI; generating trips

## Proof

`GET /health`; pytest smoke; CI workflow smoke (or documented local gate); monitor no-op without keys; evals smoke runner importable

## Explicit non-goals

- Do not pull work from later slices (no real chat/generate).
- Do not invent Wandr APIs or DTOs.
- Do not require Langfuse keys for health to pass.
