# Low-level system design (LLD)

> **Filename:** `llm.md` — LLD SSOT for humans and coding agents applying `pN-*`.  
> **Product behavior SSOT:** [`product-goal.md`](./product-goal.md)  
> **Architecture (locked L1–L24):** [`architecture-draft.md`](./architecture-draft.md)  
> **SWE / LLD regulations:** [`phase-slices/SHARED-SWE-LLD.md`](./phase-slices/SHARED-SWE-LLD.md)  
> **Fail-soft:** [`phase-slices/SHARED-FAIL-SOFT.md`](./phase-slices/SHARED-FAIL-SOFT.md)

This document is **agentic-trip** contracts only. Do **not** copy or invent Wandr `guideagent` paths, DTOs, or env vars.

---

## 1. How to use this doc

1. Open the active slice under [`phase-slices/`](./phase-slices/) (`blueprint.md` + `guardrails.md` + `validation.md`).
2. Implement **one sub-phase** (`P{n}.{m}`) at a time; meet its proof before the next.
3. Match types, functions, and routes here. If a blueprint and this file disagree, fix the docs in the same change — do not invent a third shape.
4. Next **code** OpenSpec change is `p0-foundation`, executed as P0.1 → P0.12. This LLD does not scaffold `/src` by itself.

---

## 2. Locked decisions (do not contradict)

Follow architecture L1–L24. Especially:

| ID | Rule |
|----|------|
| L6 | FastAPI modular monolith at repo root `/src` + Next.js `frontend/` |
| L7 | LangGraph; cheap dialogue vs abortable generate |
| L11 | Constrained greedy day-packer + validate; not OR-Tools in v1 |
| L12 | ARQ + Redis for long jobs (catalog acquire from P3) |
| L14 | Routers → services → ports/adapters |
| L16 | `LlmGateway` + LiteLLM; role aliases `dialogue` / `narrative` / `embed` |
| L17 | Generate = in-process SSE first; ARQ adapter later behind `GenerateRunner` |
| L18 | Guest cookie continue; v1 persist is **`draft` only** (no save API); save trip / last-trip unlock need auth (OAuth later) |
| L22 | Fail-soft every external kind |

---

## 3. Layered architecture and module map

```
frontend/ (Next.js)          src/ (FastAPI)
  app chat / map / explore     api/          HTTP routers only
                               core/         settings, logging, security
                               db/           engine, session
                               ports/        Protocol/ABC
                               modules/      feature services + repos
                               workers/      ARQ tasks
```

| Module | Owns | First real code |
|--------|------|-----------------|
| `modules/auth` | `AuthPort`, guest cookie | P0 stub, P1 adapter |
| `modules/llm` | `LlmGateway` / `LiteLlmAdapter` | P0 stub; **P2.1** live when keys exist |
| `modules/monitor` | `ObsPort`, traces/spans | P0 no-op, deepen per phase |
| `modules/evals` | golden runner | P0 smoke, P2/P4/P9 deepen |
| `modules/chat` | `ChatService`, session messages | P1 |
| `modules/geo` | `GeoGateway`, geocode | P2 |
| `modules/agents` | `dialogue_graph`, `generate_graph`, `revise_graph` | P2 / P4 / P6 |
| `modules/catalog` | acquire, retrieve, `PlaceRepository` | P3 |
| `modules/planner` | `TravelEngine`, validate | P4 |
| `modules/trips` | **draft** persist (v1); saved later; export DTO | P4 `persist_draft`, P5 export |
| `modules/explore` | near-me, last-trip | P7 |
| `modules/media` | media facade stub | P5 optional |
| `modules/booking` | hollow placeholder | P8 |
| `workers/` | `acquire_catalog` | P3 (package shell P0) |

Call chain: **routers → services → ports → adapters | repositories**. Graphs call services/ports only.

---

## 4. Class / Protocol catalog

| Name | Module | Responsibility | Key methods |
|------|--------|----------------|-------------|
| `Settings` | `core/settings.py` | env, fail-fast on boot | load via pydantic-settings |
| `get_session` | `db/session.py` | async SQLAlchemy session | `async with` |
| `LlmGateway` | `ports` / `modules/llm` | complete + later embed | `complete(role, messages, schema?)`, `embed(texts)` |
| `AuthPort` | `ports` / `modules/auth` | guest identity now | `issue_guest()`, `read_principal(request)` |
| `ObsPort` | `ports` / `modules/monitor` | traces/spans; no-op if unconfigured | `start_trace`, `span`, `generation` |
| `GeoGateway` | `ports` / `modules/geo` | geocode candidates | `search(query) -> list[GeoCandidate]` |
| `PlaceRepository` | `ports` / `modules/catalog` | PostGIS CRUD + retrieve | `upsert_many`, `retrieve(scope, prefs)` |
| `TravelEngine` | `ports` / `modules/planner` | pack days | `pack(scope, places, prefs) -> Itinerary` |
| `GenerateRunner` | `ports` / `modules/agents` | abortable generate | `start(session_id)`, `abort(session_id)` |
| `ChatService` | `modules/chat` | session + send | `create_session`, `send_message`, `get_session` |
| `CatalogService` | `modules/catalog` | acquire + retrieve | `acquire(scope)`, `retrieve(scope, prefs)`, `readiness(session_id)` |
| `TripService` | `modules/trips` | persist **draft** (v1; not saved), export | `persist_draft`, `get_trip`, `export_guidebook` |
| `ExploreService` | `modules/explore` | geo feed | `near_me(gps?, ip?)`, `last_trip(user)` |
| `BookingService` | `modules/booking` | hollow slot | `get_placeholder(trip_id)` |
| `SessionRepository` | `modules/chat` or `trips` | `TripSessionState` persist | `get`, `save` |
| `InProcessGenerateRunner` | `modules/agents` | SSE + in-process graph | implements `GenerateRunner` |
| `LiteLlmAdapter` | `modules/llm` | LiteLLM only | implements `LlmGateway` |
| `NominatimAdapter` | `modules/geo` | geocode | implements `GeoGateway` |
| `NoOpObs` | `modules/monitor` | fail-soft tracer | implements `ObsPort` |

Frontend (when the slice owns UI): `ChatShell`, `HitlChips`, **`GenerateCta` (P4.11)**, `GuidebookView`, `TripMap`, `ExploreTabs`, `BookingPlaceholder`, `PrintGuidebook`.

---

## 5. HTTP API catalog (this product)

Prefix: `/api/v1` except health. Routers depend on services only.

### 5.1 Routes

| Phase | Method + path | Service | Body / query (sketch) | Response (sketch) |
|-------|----------------|---------|------------------------|-------------------|
| P0 | `GET /health` | probe | — | `{ "status": "ok" }` |
| P0 | `GET /health/ready` | probe | — | `{ "status": "ok"\|"degraded", "db": bool }` |
| P1 | `POST /api/v1/sessions` | `ChatService.create_session` | `{}` | `{ "session_id", "guest": true }` + `Set-Cookie` |
| P1 | `POST /api/v1/sessions/{id}/messages` | `ChatService.send_message` | `{ "text" }` | SSE: `token` / `message` / `error` (P1). `hitl` from P2 |
| P1 | `GET /api/v1/sessions/{id}` | `ChatService.get_session` | — | `{ session_id, messages[], budget, hitl?, trip_scope? }` |
| P2 | `POST /api/v1/sessions/{id}/hitl` | resume HITL | `{ "choice_id" }` or `{ "text" }` | session projection |
| P3 | `GET /api/v1/sessions/{id}/catalog` | `CatalogService.readiness` | — | `{ "ready": bool, "status", "place_count"? }` |
| P3 | `POST /api/v1/catalog/acquire` | `CatalogService.acquire` | `{ "session_id" }` | `{ "job_id", "status" }` |
| P4 | `POST /api/v1/sessions/{id}/generate` | `GenerateRunner.start` | `{ }` | SSE progress + done/fail/aborted. **P4.11** Build plan CTA calls this after scope — not every chat turn |
| P4 | `POST /api/v1/sessions/{id}/generate/abort` | `GenerateRunner.abort` | `{ }` | `{ "abort_requested": true }` |
| P5 | `GET /api/v1/trips/{id}` | `TripService.get_trip` | — | trip artifact (days, stops, narratives) |
| P5 | `GET /api/v1/trips/{id}/export` | `TripService.export_guidebook` | — | `GuidebookExport` JSON |
| P5b | — (FE print + `@react-pdf/renderer`) | optional later: `GET /api/v1/trips/{id}/pdf` | — | Product path: FE print/PDF from `GuidebookExport` via `GET .../export`. Server PDF / ARQ deferred. |
| P6 | `POST /api/v1/sessions/{id}/revise` | revise use-case | `{ "text" }` | SSE or updated itinerary |
| P7 | `GET /api/v1/explore/near-me` | `ExploreService.near_me` | `lat,lng` optional | `{ "places": [] }` or honest empty |
| P7 | `GET /api/v1/explore/last-trip` | `ExploreService.last_trip` | — | places **or** `{ "locked": true }` on draft / until authenticated `saved` |
| P8 | `GET /api/v1/trips/{id}/booking` | `BookingService.get_placeholder` | — | `{ "status": "placeholder", "stays": [], "flights": [], "activities": [] }` |
| P9 | — | middleware | rate limit headers | no new product resource |

Field names above are **sketches**. Freeze Pydantic models in `p1` / `p5` code designs. Do not use Wandr field names as a source.

### 5.2 SSE event names (this product)

| Event | Phase | Payload sketch |
|-------|-------|----------------|
| `token` | P1 | incremental dialogue text |
| `message` | P1 | completed assistant message |
| `hitl` | P2 | `{ kind, candidates[] }` |
| `progress` | P4 | `{ stage, detail }` e.g. `retrieving`, `packing`, `validating`, `narrating` |
| `done` | P4/P6 | `{ trip_id? }` |
| `error` | any | `{ code, message }` honest |
| `aborted` | P4 | `{ }` |

---

## 6. Session and trip data shapes

Conceptual (architecture §5.3 / §7). Persist in Postgres; checkpoint dialogue HITL in Postgres-backed LangGraph saver.

```text
TripSessionState
├── session_id, user_id? (guest cookie)
├── messages[]
├── budget: dialogue | generate | revise
├── intent?            # duration, vibe, constraints
├── trip_scope?        # kind city|region|country; geo_id, name, bbox, hubs[], day_budget
├── hitl?              # kind, candidates[], status pending|resolved
├── catalog?           # ready, place_ids[], quality_notes
├── itinerary?         # days[] / stops[] with catalog place ids + coords
├── validation?        # pass/fail + errors
├── trip_id?
├── run?               # status, started_at, abort_requested, timed_out?
└── obs_trace_id
```

```text
TripArtifact
├── status: draft | saved     # v1 persist_draft → draft only; saved = Later/OAuth
├── days[], stops[], narratives, map   # v1 map = points only (no invented polylines)
└── booking: { status: "placeholder", stays: [], flights: [], activities: [] }
```

`GuidebookExport` (P5) is the JSON view-model for guidebook UI **and** later PDF. Source of truth is the structured trip (**draft** in v1), never LLM-written PDF prose as plan.

---

## 7. Sequences

### 7.1 Chat turn (P1)

```
Client → POST /api/v1/sessions/{id}/messages
       → ChatService.send_message
       → (P2+) dialogue_graph via services/ports
       → SSE tokens → client
Disconnect → cancel that turn’s work
```

### 7.2 HITL (P2)

```
dialogue_graph → geocode candidates ambiguous
              → interrupt + persist hitl on session
Client GET session / SSE hitl event
Client POST /api/v1/sessions/{id}/hitl { choice_id }
              → resume → confirm_scope → trip_scope
```

HITL is **not** an ARQ job.

### 7.3 Catalog acquire (P3)

```
scope ready → POST /api/v1/catalog/acquire
           → CatalogService.acquire → ARQ acquire_catalog
           → PlaceRepository.upsert_many (region/hubs only)
           → GET .../catalog { ready | failed | partial }
```

### 7.4 Generate + abort (P4)

Starts only from an **explicit** user action after `trip_scope` (P4.11 Build plan CTA → this POST). Confirming scope does not generate.

```
POST .../generate → GenerateRunner.start (in-process SSE)
  retrieve_places → TravelEngine.pack → validate_itinerary
  → (pass) write_narrative via LlmGateway(role=narrative)
  → TripService.persist_draft   # status=draft; not saved
Disconnect or POST .../abort or wall-clock timeout
  → abort_requested → cooperative cancel → no success persist
  → honest SSE aborted | error
Validation fail → do not persist success; still record eval/trace
```

### 7.5 Revise (P6)

```
POST .../revise → parse revision intent → cap checker
               → revise_graph re-enters generate with caps
               → structure + map update (not prose-only rewrite)
```

### 7.6 Explore (P7)

```
GET .../near-me → GPS if present else IP → catalog retrieve → honest empty if none
GET .../last-trip → if no authenticated saved trip (incl. guest draft): locked
                  else catalog around last saved location
```

---

## 8. Algorithms (function-level)

| Function | Module | Algorithm | Notes |
|----------|--------|-----------|--------|
| `pack_days` | `TravelEngine` | Constrained greedy: assign catalog stops to days under time/walk/transfer caps; hub sequence for region trips | O(n log n) typical sort + linear assign; not OR-Tools |
| `validate_itinerary` | `planner` | Hard gates: every stop id ∈ retrieved catalog; country filter; day caps; transfer sanity | Pure code |
| `haversine_meters` | `planner` | Spherical distance | Fail-soft times when OSRM missing |
| `travel_matrix` | `planner` | OSRM table else haversine + penalty | No geometry invention |
| `retrieve_places` | `PlaceRepository` | PostGIS bbox ∩ category/tags; GiST | Vectors later |
| `classify_scope` | `geo` / agents | Admin level + bbox span + place class; country-long writes `hubs[]` or HITL; LLM hubs only if thin country | Never silent country centroid |
| `geocode_search` | `GeoGateway` | Return ranked candidates | HITL if ambiguous |
| `near_me` | `ExploreService` | GPS → IP → retrieve | Honest empty |
| `acquire_catalog` | worker | Bounded retry; region/hubs polygons only | Mark failed |

Upgrade path: 2-opt or OR-Tools **behind the same** `TravelEngine.pack`.

---

## 9. Consistency / SWE regulations

Follow [`phase-slices/SHARED-SWE-LLD.md`](./phase-slices/SHARED-SWE-LLD.md) in full. Short form:

- Naming: `*Service`, `*Port`/`*Gateway`, `*Repository`, `*Adapter`.
- One use-case per service method.
- Fail-soft adapters; honest services.
- Tests at the layer that owns the logic.

---

## 10. Sub-phase index

| Sub-phase | LLD section | Primary functions / types |
|-----------|-------------|---------------------------|
| P0.1–P0.3 | §3 skeleton, db | `Settings`, `get_session` |
| P0.4–P0.9 | §4 stubs | all Protocols no-op/stub |
| P0.10 | §5 health | `GET /health`, `/health/ready` |
| P0.11–P0.12 | workers, tests | import smoke |
| P1.1–P1.9 | §5 sessions, §7.1 | `ChatService`, cookie `AuthPort` |
| P2.1 | §4 `LiteLlmAdapter` | live gateway when keys exist; stub if missing |
| P2.1–P2.9 | §7.2, `classify_scope` | `dialogue_graph`, HITL route; country-long hubs/HITL |
| P3.1–P3.8 | §7.3, retrieve | `CatalogService`, ARQ |
| P4.1 / P4.8 | §7.4 timeout + abort | wall-clock timeout shares abort path |
| P4.1–P4.10 | §7.4, §8 pack/validate | `GenerateRunner`, `TravelEngine`, `persist_draft` |
| P4.11 | §5 generate POST | FE Build plan CTA after scope |
| P5.1–P5.6 | §5 trips, `GuidebookExport` | map + guidebook; **v1 points-only** |
| P5b.1–P5b.4 | export DTO only | print/pdf, no LLM |
| P6.1–P6.5 | §7.5 | `revise_graph`, caps |
| P7.1–P7.5 | §7.6 | `ExploreService` |
| P8.1–P8.5 | booking field | `BookingService` |
| P9.1–P9.5 | evals/CI | caps, abort, rate limit |

Full headings live in each slice `blueprint.md`.

---

## 11. Non-goals

- Wandr OpenAPI, DTOs, env vars, or `guideagent` routes.
- Live lodging/flight checkout, fake rates.
- Qdrant / pgvector required on day one.
- OAuth in P0–P1 (port + guest only).
- OR-Tools / full optimizer in v1.
- Media enrich or PDF on generate hot path.
- Microservices split; FE as a separate repo (stays `frontend/`).
- Scaffolding `/src` in the docs change that added this file — that is OpenSpec `p0-foundation`.
