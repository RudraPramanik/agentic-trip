## Context

See `proposal.md` for motivation. Settled product/architecture remain `system-docs/chat-first-trip-os.md` and `system-docs/architecture-draft.md` (L1–L24). Slice folders already exist under `system-docs/phase-slices/` with thin `blueprint.md` step plans. This change deepens those packages **in place** and adds `system-docs/llm.md`. It does **not** scaffold `/src`.

Normative delivery behavior: `specs/phase-slice-lld/spec.md`.

## Goals / Non-Goals

**Goals:**

- Lock a sub-phase numbering scheme and a per-sub-phase blueprint section shape (modules, classes/functions, services, routes/APIs, DTOs, proof).
- Lock the sub-phase catalog for every existing slice so apply is fill-in, not invention.
- Lock shared SWE/LLD/algorithm/system-design guardrail sources plus per-slice deltas.
- Lock `system-docs/llm.md` as LLD SSOT (this product’s modules, APIs, sequences, algorithms).
- Keep one-phase proofs: sub-phase gates inside a slice; slice validation still blocks the next phase.

**Non-Goals:**

- Runtime code, Docker images, or frontend features.
- Changing L11 (constrained greedy packer), L17 (in-process SSE generate), or other locked architecture decisions.
- Nested `p0.1/` directories or a second OpenSpec change per sub-phase (optional later; not this apply).
- Final LiteLLM model id strings, OAuth provider, or Qdrant.

## Decisions

### D1 — Sub-phases live inside existing blueprints

**Choice:** Numbered headings in `blueprint.md` (`### P0.1 …`). Keep folders `p0-foundation`, `p1-chat`, … `p9-hardening`.

**Why:** User asked for splits *inside* existing blueprints; nested packages would duplicate the catalog and break the archived `phase-slices-program` layout.

**Alternatives:** Nested folders per sub-phase (rejected); one OpenSpec change per sub-phase now (rejected — too many empty changes before `/src` exists). Later code applies remain one OpenSpec change per **phase**, executed sub-phase-by-sub-phase using the blueprint.

### D2 — Sub-phase section template

Every sub-phase heading in a blueprint MUST use this shape (fill all rows; use `—` only when truly N/A):

```
### P{n}.{m} — <short name>

- **Goal:** one sentence
- **Modules:** `src/...` and/or `frontend/...`
- **Types:** classes / Protocols / Pydantic DTOs / FE components
- **Functions:** named functions or methods in scope (function-level)
- **Services:** application services / use-cases
- **Routes / APIs:** `METHOD /api/v1/...` (this product only) or `none`
- **Algorithms / data:** complexity or index notes when relevant
- **Depends on:** prior sub-phases in this slice
- **Proof:** runnable or reviewable check
- **Non-goals:** what this sub-phase must not pull in
```

Phase-level Goal / Scope / Proof / Non-goals stay at the top of the file as the slice summary.

### D3 — HTTP catalog prefix for this product

**Choice:** Document this product’s HTTP under `/api/v1/`. Names below are **agentic-trip** contracts for `llm.md` + blueprints, not Wandr.

**Why:** Architecture did not lock paths; implementers need a single catalog. Prefix is stable; handlers stay thin.

**Alternatives:** Unversioned `/chat` (rejected — harder to evolve); copying Wandr `guideagent` paths (forbidden).

Locked route inventory (document in `llm.md`; only the owning sub-phase implements):

| Phase | Method + path | Owner service |
|-------|----------------|---------------|
| P0 | `GET /health` | health/ready probe |
| P0 | `GET /health/ready` | DB/deps probe |
| P1 | `POST /api/v1/sessions` | `ChatService` / session create |
| P1 | `POST /api/v1/sessions/{id}/messages` | `ChatService.send` (SSE) |
| P1 | `GET /api/v1/sessions/{id}` | session projection (messages, hitl, budget) |
| P2 | `POST /api/v1/sessions/{id}/hitl` | HITL resume / chip choice |
| P3 | `GET /api/v1/sessions/{id}/catalog` | catalog readiness |
| P3 | `POST /api/v1/catalog/acquire` | enqueue acquire (or session-scoped equivalent) |
| P4 | `POST /api/v1/sessions/{id}/generate` | `GenerateRunner.start` (SSE) |
| P4 | `POST /api/v1/sessions/{id}/generate/abort` | `abort_requested` |
| P5 | `GET /api/v1/trips/{id}` | trip + guidebook view |
| P5 | `GET /api/v1/trips/{id}/export` | `GuidebookExport` DTO |
| P5b | `GET /api/v1/trips/{id}/pdf` | optional; FE print may suffice |
| P6 | `POST /api/v1/sessions/{id}/revise` | capped replan (SSE or result) |
| P7 | `GET /api/v1/explore/near-me` | `ExploreService.near_me` |
| P7 | `GET /api/v1/explore/last-trip` | last-trip after **saved** trip |
| P8 | `GET /api/v1/trips/{id}/booking` | placeholder payload |
| P9 | (no new product surface required) | middleware + CI |

Routers MUST only depend on services. Paths MUST NOT mimic Wandr.

### D4 — Layering in LLD (consistency)

**Choice:** Repeat architecture §12 as the only allowed call chain:

`api routers` → `application services` → `ports (Protocol/ABC)` → `adapters | repositories`

**Rules to copy into shared SWE/LLD guardrails:**

- One use-case per service method; no God-service across chat + booking + PDF.
- Agents/graphs call services/ports only; no SQL or vendor `httpx` in graphs.
- Pydantic at HTTP edges; domain models inward; no DTO leakage into engine internals.
- DI via constructors / FastAPI `Depends`; adapters swapped in composition root (`main.py`), not imported from routers.
- Idempotent writes where retries exist (acquire job, abort flag).
- Fail-soft adapters return typed empty/error results; services map to honest user outcomes.
- Naming: `*Service`, `*Port`/`*Gateway`, `*Repository`, `*Adapter`, `*Router`.
- Tests: unit at engine/validate/classify; API tests at routers; goldens at dialogue/generate.

**Anti-patterns (never):** vendor SDK in router; invented coords; unbounded ReAct; country-centroid scrape; LLM stop-order.

### D5 — Algorithms (lock, do not “optimize later” in v1)

Document in `llm.md` + P3/P4/P6/P7 guardrails:

| Concern | v1 algorithm | Why |
|---------|--------------|-----|
| Day packing | Constrained greedy packer (L11) + hard validate | Goldens fail on invented POIs first, not 3% walk |
| Local improve | None in v1; 2-opt / OR-Tools only behind `TravelEngine` later | Same port |
| Travel times | OSRM table if present else haversine + penalty; **no fake polylines** | Fail-soft routing |
| Retrieve | PostGIS bbox + category/tags; GiST on geometry | Vectors deferred (L9) |
| Geocode pick | Never silent; HITL if ambiguous | Bible |
| Scope classify | Deterministic geo metadata first; LLM hubs only if thin country | Bible |
| Near me | GPS then IP; honest empty | Bible |
| Catalog acquire | Bounded ARQ; region/hubs only | L12, no centroid scrape |
| Generate abort | Disconnect + `abort_requested` cooperative cancel | L17 |

Complexity notes belong on the sub-phase that owns the function (`pack_days`, `retrieve_places`, `haversine`).

### D6 — Shared guardrail files

**Choice:**

- Keep `SHARED-FAIL-SOFT.md` as fail-soft snippet.
- Add `system-docs/phase-slices/SHARED-SWE-LLD.md` for architecture, algorithms, system-design, and LLD consistency rules (the “regulations” list).
- Each slice `guardrails.md` = fail-soft table (slice rows) + “SWE/LLD delta” bullets that specialize the shared file (e.g. P4: packer + validate purity).
- `_template/guardrails.md` links both shared files and includes empty tables/sections.

**Why:** One SSOT for rules; slices stay short; template prevents empty copies.

**Alternatives:** Stuff all rules only into `llm.md` (rejected — implementers opening a slice would miss them); duplicate the full list in every slice (rots).

### D7 — `system-docs/llm.md` structure

**Choice:** Single LLD file at `system-docs/llm.md` (filename per request; title **Low-level system design**). Audience: humans and coding agents applying `pN-*`.

Required sections:

1. How to use this doc (read with the active slice blueprint + guardrails).
2. Locked decisions pointer (architecture L1–L24; do not restated contradictions).
3. Layered architecture + module map (`src/modules/*`, ports, workers, frontend).
4. Class/Protocol catalog (tables: name, module, responsibilities, key methods).
5. HTTP API catalog (D3) + request/response field sketches (this product).
6. Session/trip data shapes (from architecture §5.3 / §7) — conceptual, not Wandr.
7. Sequence diagrams: chat turn, HITL, catalog acquire, generate+abort, revise, explore.
8. Algorithms (D5) with function names matching blueprints.
9. Consistency / SWE regulations (pointer to `SHARED-SWE-LLD.md`).
10. Sub-phase index (table: sub-phase id → LLD section / functions).
11. Explicit non-goals (Wandr, booking vendors, Qdrant-on-day-one, …).

**Why:** One file coding agents can load; blueprints stay per-phase; architecture stays high-level.

**Alternatives:** Per-slice `lld.md` (rejected for this change — user asked for one `llm.md`); repo-root `LLM.md` only (rejected — SSOT lives with `system-docs`).

### D8 — Sub-phase catalog (locked for apply)

Apply writes these headings into each existing `blueprint.md`. Counts may grow by **at most one** clarifying split if a heading is still too large; do not collapse.

**P0 Foundation**

| ID | Name | Core units |
|----|------|------------|
| P0.1 | Repo skeleton | `pyproject.toml`, `src/` package, `Dockerfile`, `docker-compose` (`api`,`db`) |
| P0.2 | Settings + logging | `core/settings.py`, `core/logging.py` |
| P0.3 | DB session + Alembic | `db/session.py`, `alembic/` baseline |
| P0.4 | Ports package | Protocols: `LlmGateway`, `AuthPort`, `ObsPort`, `GeoGateway`, `GenerateRunner`, `TravelEngine`, `PlaceRepository` (stubs OK) |
| P0.5 | Feature module shells | empty `modules/{chat,geo,catalog,planner,trips,explore,media,booking,llm,agents,auth,monitor,evals}` importable |
| P0.6 | Guest AuthPort stub | cookie identity functions; no OAuth |
| P0.7 | LlmGateway stub | structured unavailable if keys missing |
| P0.8 | Monitor no-op | `ObsPort` no-op tracer |
| P0.9 | Evals smoke | importable runner; `tests/evals` placeholder |
| P0.10 | Health API + app entry | `GET /health`, `GET /health/ready`, `main.py` router include |
| P0.11 | Workers placeholder | `workers/` package; no ARQ required |
| P0.12 | Pytest + CI smoke | health test; module import test; optional frontend stub |

**P1 Chat**

| ID | Name | Core units |
|----|------|------------|
| P1.1 | Guest cookie adapter | `AuthPort` cookie issue/read |
| P1.2 | Session model + repo | `TripSessionState` persist |
| P1.3 | Chat DTOs + `ChatService` | create session, append message |
| P1.4 | Create session route | `POST /api/v1/sessions` |
| P1.5 | Send message SSE | `POST /api/v1/sessions/{id}/messages` |
| P1.6 | Session get + SSE abort | `GET /api/v1/sessions/{id}`; cancel on disconnect |
| P1.7 | Chat traces | obs spans on turn |
| P1.8 | FE chat shell | stream client; no generate button required |
| P1.9 | Proof tests | guest round-trip |

**P2 Dialogue + scope + HITL**

| ID | Name | Core units |
|----|------|------------|
| P2.1 | Intent schema + parse | structured out via `LlmGateway` role `dialogue` |
| P2.2 | GeoGateway + geocode adapter | Nominatim-class; candidates only |
| P2.3 | `geocode_search` service | never silent pick |
| P2.4 | `classify_scope` | deterministic metadata first |
| P2.5 | `dialogue_graph` + interrupt | LangGraph HITL |
| P2.6 | HITL projection + resume API | `POST /api/v1/sessions/{id}/hitl` |
| P2.7 | `confirm_scope` | writes `trip_scope` |
| P2.8 | FE HITL chips | in-chat |
| P2.9 | Scope goldens | city/region/country/Paris/Meghalaya/Japan |

**P3 Catalog**

| ID | Name | Core units |
|----|------|------------|
| P3.1 | Place model + PostGIS repo | GiST geometry |
| P3.2 | Places adapters | Overpass/OTM behind facade |
| P3.3 | `CatalogService.acquire` | region/hubs only |
| P3.4 | ARQ `acquire_catalog` | bounded retry; Redis+worker |
| P3.5 | `retrieve_places` | bbox/category/tags |
| P3.6 | Catalog HTTP | readiness + acquire enqueue |
| P3.7 | Retrieve spans | obs |
| P3.8 | Proof tests | real ids or honest empty |

**P4 Generate**

| ID | Name | Core units |
|----|------|------------|
| P4.1 | `GenerateRunner` + in-process SSE | progress events |
| P4.2 | `TravelEngine.pack` | constrained greedy |
| P4.3 | Travel matrix | OSRM or haversine+penalty |
| P4.4 | `validate_itinerary` | catalog grounding, caps, country filter |
| P4.5 | `generate_graph` nodes | retrieve → pack → validate → narrative → persist |
| P4.6 | Narrative via gateway | role `narrative`; no stop invention |
| P4.7 | Draft persist | validation must pass |
| P4.8 | Abort | disconnect + abort route |
| P4.9 | Generate HTTP | `POST .../generate` SSE |
| P4.10 | Generate goldens | Meghalaya/Japan-shaped |

**P5 Guidebook + map**

| ID | Name | Core units |
|----|------|------------|
| P5.1 | `GuidebookExport` DTO | JSON = future PDF input |
| P5.2 | Trip get + export routes | |
| P5.3 | FE guidebook | cover, hubs, per-leg |
| P5.4 | MapLibre | points; polyline only if geom |
| P5.5 | Empty booking block in UI | no rates |
| P5.6 | Media facade stub | not on generate hot path |

**P5b PDF**

| ID | Name | Core units |
|----|------|------------|
| P5b.1 | Print CSS from export DTO | |
| P5b.2 | react-pdf (optional) | same DTO |
| P5b.3 | Download/print action | `GET .../pdf` or FE-only |
| P5b.4 | No LLM on PDF path | |

**P6 Revision**

| ID | Name | Core units |
|----|------|------------|
| P6.1 | Parse revision intent | structured |
| P6.2 | Cap checker | loop/day/walk budgets |
| P6.3 | `revise_graph` | re-enter generate with caps |
| P6.4 | Revise HTTP | SSE or result |
| P6.5 | Structure+map update proof | e.g. less walking day 2 |

**P7 Explore**

| ID | Name | Core units |
|----|------|------------|
| P7.1 | GPS→IP `near_me` | honest empty |
| P7.2 | `last_trip` after saved trip | locked pre-save |
| P7.3 | Explore HTTP | near-me + last-trip |
| P7.4 | FE dual-tab | |
| P7.5 | Proof tests | no fake POIs |

**P8 Booking placeholder**

| ID | Name | Core units |
|----|------|------------|
| P8.1 | Booking field on trip | `status=placeholder` |
| P8.2 | Hollow `BookingService` | no vendors |
| P8.3 | Booking GET | |
| P8.4 | FE placeholder | |
| P8.5 | Save without rates | |

**P9 Hardening**

| ID | Name | Core units |
|----|------|------------|
| P9.1 | Golden CI gate | fail build on regression |
| P9.2 | Cost caps | tests |
| P9.3 | Abort harden | multi-instance / Redis flag if needed |
| P9.4 | Rate limit middleware | |
| P9.5 | Harness pass | evals module deepened |

### D9 — Validation.md shape

Each `validation.md` gains a **Sub-phase checks** table (ID → proof). Existing Checks / CI / Exit criteria remain. Exit criteria MUST say: all sub-phase proofs + phase checks.

### D10 — Docs index / architecture sync

- `phase-slices/README.md`: delivery loop includes sub-phases + `llm.md`.
- `architecture-draft.md` §14–§15: sub-phase inside slice; package table adds LLD pointer; changelog.
- `system-docs/README.md`: row for `llm.md`.
- Slice `references.md`: link `llm.md` + `SHARED-SWE-LLD.md`.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| LLD and architecture drift | `llm.md` points at L-decisions; conflict rule in spec; changelog on architecture when paths lock |
| Blueprints become huge | Sub-phase template is tabular/bullets; algorithms live mainly in `llm.md` + shared rules |
| Inventing too much HTTP now | Catalog is this product’s; fields stay sketches; no Wandr names |
| Apply is a large docs edit | Tasks are per-slice file groups; catalog in D8 is the fill-in SSOT |
| Later code ignores sub-phases | Spec + validation checklists; `pN` OpenSpec tasks should map 1:1 to sub-phase IDs |

## Migration Plan

1. Apply this change: write `llm.md`, `SHARED-SWE-LLD.md`, deepen every slice, update template/indexes/architecture.
2. Proof: every blueprint has `P{n}.1`+ sections per D8; every guardrails has SWE/LLD section; `llm.md` has API catalog; `openspec validate --strict`.
3. Next code change remains `p0-foundation`, executed as P0.1 → P0.12.
4. Rollback: revert the docs change; product specs unchanged.

## Open Questions

1. Exact Pydantic field names for session/export DTOs — sketch in `llm.md` during apply; freeze in `p1`/`p5` code designs.
2. Whether `GET /api/v1/trips/{id}/pdf` is needed vs FE print-only — P5b blueprint lists both; choose at `p5b-pdf-export` code time without changing this spec.
