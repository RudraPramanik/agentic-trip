## Context

See `proposal.md` for why. This repo has no `/src` yet. Implementation follows `system-docs/phase-slices/p0-foundation/` (P0.1–P0.12, including `guardrails.md` and `validation.md`), `system-docs/llm.md` §3–5, `system-docs/phase-slices/SHARED-SWE-LLD.md`, and `system-docs/phase-slices/SHARED-FAIL-SOFT.md`. Architecture L6/L14/L20/L22/L24 are locked: FastAPI modular monolith at repo root, routers → services → ports, fail-soft obs, `monitor/` + `evals/` shells.

SWE, reliability, and scale are **already owned by phase-slices**. This design only freezes P0 numbers and names. Later slices keep their owners (P1 session cookie + ownership, P3 ARQ + GiST retrieve, P4 abort/timeout, P9 rate limit + multi-instance abort). Do not pull those into this change.

Product-goal P0 ships an empty shell plus health — not a guest chat journey, not a draft trip, and not last-trip Explore. v1 persist remains a later-slice `draft`; P0 must not invent a fake user or save API.

## Goals / Non-Goals

**Goals:**

- A bootable API image and Compose `api` + PostGIS `db`.
- Health vs ready split that orchestration can use.
- Ports and feature shells that later slices fill without inventing layout.
- Fail-soft stubs so missing Langfuse/LLM keys never block health.
- SWE layering from the first file: routers parse HTTP; composition root wires stubs; no vendor SDKs in routers.

**Non-Goals:**

- Chat, HITL, catalog, generate, Explore, booking HTTP (`/api/v1/…` product routes).
- Redis, ARQ jobs, Qdrant, Next.js app, OAuth, live LiteLLM.
- A feature-module `HealthService` (blueprint: ready is a DB ping, not a product use-case).
- Rate limits, generate timeout seconds, catalog cache, OSM User-Agent (owned by later slices).
- Wandr paths, DTOs, cookie names, or env vars.
- Invented coordinates, venues, or polylines.

## Decisions

### D1 — Python package layout is `src.*`

P0.5 proof requires `import src.modules.<name>`. Keep that: `src/` is the installable package (`pyproject.toml` packages `{ include = "src" }` or equivalent package-dir mapping so `src.main:app` works).

**Why not** a prettier `agentic_trip` top-level name: the LLD and slice proofs already specify `src.modules`. Renaming now would fork docs and code.

**Alternative considered:** `backend/` package. Rejected (architecture L20).

### D2 — Tooling: Python 3.12 + `uv` + `pyproject.toml`

Use **Python 3.12**, **uv** for lock + scripts, pytest via `uv run pytest`. Pin FastAPI, uvicorn[standard], pydantic-settings, sqlalchemy[asyncio], asyncpg, alembic, structlog, httpx, pytest, pytest-asyncio.

**Why uv:** fast, lockfile, one installer for local and CI. **Why not Poetry:** extra tool; uv is enough. **Why not unpinned pip-only:** CI unreproducible.

### D3 — Required vs optional settings

Required at boot (fail-fast):

- `DATABASE_URL` (async Postgres DSN)

Optional (must not block boot or `/health`):

- Langfuse / obs keys
- LLM provider keys
- `CORS_ALLOWED_ORIGINS` (default `http://localhost:3000` for later FE; unused by P0 routes)

**Why not** require LLM keys for health: P0.2 / P0.7 / fail-soft law.

Do **not** copy Wandr env names (`AUTH0_*`, `wandr_*`, `guideagent`).

### D4 — Health vs ready

| Path | Meaning | DB down |
|------|---------|---------|
| `GET /health` | liveness | **200** `{ "status": "ok" }` |
| `GET /health/ready` | dependency probe | **503** `{ "status": "degraded", "db": false }` |

Ready success: **200** `{ "status": "ok", "db": true }`. Ready pings DB with a short timeout (5s). Liveness does not touch the DB.

**Why 503 not 200-degraded:** Kubernetes/Compose restart policies treat non-2xx as not-ready. Blueprint allowed “degraded/fail”; 503 is the concrete pick.

Routers live in `src/api/health.py` and **only** parse/serialize HTTP (SWE: no SQL, no vendor SDKs, no business rules). Ready pings the database through a small helper on the session factory (`src/db/session.py`, e.g. `ping_db()`), injected via FastAPI `Depends` — not a feature-module `HealthService`, and not SQLAlchemy in the router.

`create_app()` in `src/main.py` is the composition root: wires stub adapters (`StubAuthAdapter`, `StubLlmGateway`, `NoOpObs`), never constructs vendors in routers.

### D5 — Database session

`src/db/session.py`: SQLAlchemy async engine + `async_sessionmaker`. `pool_pre_ping=True`. Default pool size (SQLAlchemy defaults) is enough for P0; do not tune for multi-worker generate.

Alembic at repo root; baseline revision with empty metadata besides whatever SQLAlchemy needs. No place/trip tables.

Compose `db`: `postgis/postgis:16-3.5` (or current 16-3.x), healthcheck, `api` depends_on healthy db.

### D6 — Ports and stubs

`src/ports/` holds Protocols: `LlmGateway`, `AuthPort`, `ObsPort`, `GeoGateway`, `GenerateRunner`, `TravelEngine`, `PlaceRepository`. Abstract methods only (or `NotImplementedError`). Port types stay provider-free (no LiteLLM/Nominatim/Langfuse types).

`LlmGateway` matches `llm.md` §4: `complete(role, messages, schema=None)` and `embed(texts)`. The P0.4 blueprint currently lists `complete` only — this change updates that method list in the same apply so blueprint and LLD do not fork. P0.7 proof remains `complete` without keys → `LlmUnavailable`. `embed` on the stub returns the same structured unavailable (or `NotImplementedError`); live embeddings stay P2.

Adapters this slice:

- `StubAuthAdapter` — issues a UUID guest id; cookie name **`at_guest`** (httpOnly; Secure in non-local; SameSite=Lax). Not `wandr_session`.
- `StubLlmGateway` — `complete(...)` returns structured `LlmUnavailable`; does not raise.
- `NoOpObs` — `start_trace` / `span` / `generation` no-ops.

P1 owns signed cookie + session ownership checks. P0 only proves issue/read on a fake request. Do not persist guests to a user table.

### D7 — Feature shells and workers

Importable packages, no I/O: `chat`, `geo`, `catalog`, `planner`, `trips`, `explore`, `media`, `booking`, `llm`, `agents`, `auth`, `monitor`, `evals`. `src/workers/` exists; API tests pass with Redis absent.

`tests/evals/` collects; `EvalRunner.run_smoke()` asserts health import. No Meghalaya goldens.

### D8 — CI

GitHub Actions: checkout, uv, `uv run pytest`. Job uses a PostGIS service for `/health/ready` tests; unit tests for settings/obs/llm stubs do not need it. No Redis service.

Optional `frontend/` directory with `.gitkeep` only (P0.12). No Next.js app.

### D9 — Later-slice scale / reliability (do not implement here)

| Concern | Owner | P0 action |
|---------|--------|-----------|
| Guest cookie + CORS + session ownership | P1 | Name cookie `at_guest` only |
| Nominatim timeout + User-Agent | P2 | Port stub only |
| ARQ acquire, GiST retrieve, idempotent jobs | P3 | `workers/` placeholder |
| Generate abort + wall-clock timeout | P4 | `GenerateRunner` Protocol only |
| Rate limit, cost caps, multi-instance abort flag | P9 | nothing |

Leftover doc wording (`persist_trip` in P4.5, `phase-slices/` at repo root in the architecture tree) is **not** this change. Fix in the owning slice’s later OpenSpec design.

### D10 — Sub-phase proof gate

Implement **one** numbered sub-phase at a time (P0.1 → P0.12). Do not start P0.{m+1} until P0.{m} proof in the blueprint/validation gate is satisfied. Pytest/CI in P0.12 is the phase-level gate; it does not license skipping earlier proofs.

## Risks / Trade-offs

- **[Risk] `src` as the Python package name is unconventional** → Mitigation: follow locked proofs; document `uv run uvicorn src.main:app` in README.
- **[Risk] Empty module shells rot** → Mitigation: P0.5 import tests; later slices fill in place rather than inventing new folders.
- **[Risk] Windows Docker Desktop flakes on PostGIS healthcheck** → Mitigation: documented local compose command; CI uses a service container; unit tests don’t require Docker.
- **[Trade-off] No rate limits until P9** → Acceptable: no public traffic; don’t fake middleware in P0.

## Migration Plan

Greenfield. Land `/src` + Compose + CI on the working branch. Rollback = revert the change; nothing production-facing exists.

## Open Questions

None that affect this slice. LiteLLM model IDs, OAuth provider, generate timeout seconds, and rate-limit fail-open vs fail-closed stay with P2 / Later / P4 / P9.
