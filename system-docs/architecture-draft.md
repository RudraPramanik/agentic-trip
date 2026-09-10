# Architecture draft — agentic-trip

> **Status:** DRAFT / living decisions (not SSOT yet).  
> **SSOT product behavior:** [`chat-first-trip-os.md`](./chat-first-trip-os.md)  
> **Free media/map notes:** [`free-media-map-guidebook.md`](./free-media-map-guidebook.md)  
> **Rule:** Edit this file as we settle; promote stable sections into the bible / OpenSpec when finalized. Do not treat undecided items as build law.

Last updated: 2026-09-11 (exploration session — HITL, workers, evals, SWE layering)

---

## 1. Locked decisions (from exploration)

| # | Decision | Notes |
|---|----------|--------|
| L1 | **Guidebook target** = Layla-shaped trip artifact (cover, hub sequence, per-leg narrative, POIs, map) | PDF/print is a later surface; UI guidebook first is OK |
| L2 | **Hotels / flights / affiliate / priced activities** = **not** in v1 fulfillment | Empty **booking placeholder** in architecture + UI slot |
| L3 | Booking later is **optional** for the user | User may ignore booking, or scroll AI-assisted options when that module exists |
| L4 | **Goldens include both** Meghalaya (region / multi-hub trek) **and** Japan (country / day-budget) | Plus existing bible cases (Kyoto city, ambiguous Paris, etc.) |
| L5 | **Build one phase at a time** | P(n) done + proof before P(n+1); no day-one kitchen sink |
| L6 | **Stack:** FastAPI modular monolith (Docker) + Next.js in `frontend/` (runs separately) | BE compose for API + data deps; FE not forced into same container |
| L7 | **LangGraph** for agent orchestration | Dialogue stays cheap; generate is an explicit abortable run (see §5) |
| L8 | **Free APIs first**, paid behind facades | Mirror `MEDIA_SOURCES` / places-facade pattern |
| L9 | Vector DB **not** required on day one | See §6 — PostGIS first; **Qdrant** when vectors earn their keep |
| L10 | **HITL** = LangGraph `interrupt` + durable checkpointer | FE also sees projected `hitl` on session; see §5.6 |
| L11 | **P4 travel engine** = constrained greedy day-packer (+ validate gate) | Not full OR-Tools optimizer in v1; see §5.7 |
| L12 | **Background jobs** = **ARQ** + Redis (FastAPI-friendly) | Catalog acquire, media enrich, long generate, eval runs; see §4.4 |
| L13 | **PDF** = guidebook UI first; export via FE (print / react-pdf); optional BE job later | Not an LLM inventing PDF content; see §7 |
| L14 | **SWE shape** = feature modules + service protocols/ABCs + repositories | Smooth later CRUD/provider swaps; see §12 |
| L15 | **AI eng from early** = tracing + offline goldens skeleton in P0; deepen each phase | Langfuse-class traces; retrieval + agent spans; see §13 |

---

## 2. Product goal (working one-liner)

Guest chats a vibe or place → system HITLs scope → builds a **catalog-grounded multi-day trip** with map → user revises in chat → opens a **Layla-like guidebook** (booking slot empty until later). Explore is a parallel geo feed. Agentic booking is optional and trip-keyed after save.

---

## 3. Repo layout (proposed)

Production-common monorepo shape for a single product (not a polyrepo yet):

```
agentic-trip/
├── backend/                 # FastAPI modular monolith
│   ├── app/
│   │   ├── main.py
│   │   ├── api/             # HTTP routers
│   │   ├── core/            # settings, logging, security
│   │   ├── db/              # SQLAlchemy, Alembic
│   │   ├── modules/
│   │   │   ├── chat/        # sessions, SSE/stream
│   │   │   ├── geo/         # single geo gateway
│   │   │   ├── catalog/     # acquire + retrieve
│   │   │   ├── planner/     # travel engine + validate
│   │   │   ├── trips/       # trip artifact persistence
│   │   │   ├── explore/     # near-me + last-trip
│   │   │   ├── media/       # media facade (post-generate)
│   │   │   ├── booking/     # hollow placeholder module
│   │   │   ├── llm/         # LiteLLM gateway only
│   │   │   ├── agents/      # LangGraph graphs + state
│   │   │   └── obs/         # tracing, evals hooks
│   │   └── workers/         # optional later (enrich jobs)
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── README.md
├── frontend/                # Next.js App Router
│   ├── app/
│   ├── components/
│   ├── features/            # chat, trip, explore, map
│   ├── lib/
│   ├── package.json
│   └── README.md
├── docker-compose.yml       # backend + postgres(+postgis) + redis?; qdrant when needed
├── openspec/
└── system-docs/
```

**Why these package names**

| Path | Why |
|------|-----|
| `backend/` + `frontend/` | Clear, common for product monorepos; matches “FE folder, BE Docker” |
| `app/modules/*` | Modular monolith seams without microservices |
| `app/agents/` | Keeps LangGraph next to domain modules, not mixed into routers |
| `features/` on FE | Mirrors product surfaces (chat / trip / explore) |

**Alternatives we are not using yet:** `apps/api` + `apps/web` (Turborepo-style) — fine later if the repo grows; overkill for v1.

---

## 4. Backend / frontend package sets (production-common)

### 4.1 Backend (Python) — suggested

| Concern | Package | When |
|---------|---------|------|
| API | `fastapi`, `uvicorn[standard]` | P0 |
| Settings | `pydantic`, `pydantic-settings` | P0 |
| DB | `sqlalchemy[asyncio]`, `asyncpg`, `alembic` | P0–P1 |
| Geo SQL | PostGIS via SQLAlchemy/geoalchemy2 | P2–P3 |
| HTTP clients | `httpx`, `tenacity` | P2+ |
| LLM gateway | `litellm` | P1–P2 |
| Agent graphs | `langgraph`, `langchain-core` | P2+ (dialogue); P4 generate |
| Structured output | pydantic models + LLM json/schema | P2 |
| Cache / queue / abort | `redis` + **`arq`** | Redis with ARQ when first background job lands (often P3 acquire); abort harden P9 |
| Vector (later) | `qdrant-client` | When catalog text exists (§6); pgvector is alt, not default |
| Observability | `structlog` + **Langfuse** (or OTEL→Langfuse) | **Skeleton P0**; wire real spans as features land (§13) |
| Checkpointer | LangGraph Postgres saver (preferred) | HITL resume; avoid Redis-only checkpoint as sole source of truth |
| Tests / evals | `pytest`, `pytest-asyncio`, `httpx` ASGI; golden fixtures | From P0; expand per phase |
| PDF (later) | FE print / `@react-pdf/renderer`; optional ARQ render job | After guidebook UI — structured trip in, bytes out |

### 4.2 Frontend (Next.js) — suggested

| Concern | Package | When |
|---------|---------|------|
| App | Next.js (App Router) + TypeScript | P1 |
| Data | `@tanstack/react-query` | P1 |
| Map | `maplibre-gl` (+ react wrapper if desired) | P5 |
| Validation | `zod` | P1 |
| Styles | follow existing design system when chosen; avoid purple-AI defaults | P1+ |
| PDF | browser print CSS first; `@react-pdf/renderer` later | after guidebook UI |

### 4.3 Docker services (phased)

| Service | Introduce |
|---------|-----------|
| `api` (FastAPI) | P0 |
| `db` (Postgres + PostGIS) | P0–P1 |
| `redis` | When ARQ or multi-instance abort needs it (often ≤P3) |
| `worker` (ARQ) | Same moment as first long job (catalog / generate / media) |
| `qdrant` | **deferred** until retrieve needs vectors (§6) |

### 4.4 Workers (ARQ)

**Choice:** [ARQ](https://github.com/python-arq/arq) on Redis — modern, async-native, common with FastAPI; lighter than Celery for this monolith.

| Job | Phase | Notes |
|-----|-------|--------|
| `acquire_catalog` | P3 | Timeouts, retries, fail-soft readiness |
| `run_generate` | P4+ | Optional: move off request thread when SSE + long engine; honor `abort_requested` |
| `enrich_place_media` | media later | Never on generate hot path |
| `run_eval_suite` | P0 skeleton → P9 | Offline goldens in CI/worker |
| `render_pdf` (optional) | after P5 | Only if FE export is not enough; input = saved trip JSON |

**Not for HITL waits.** HITL is interactive graph interrupt, not a queue job.

---



## 5. LangGraph — agents, tools, state (discussion draft)

### 5.1 Two budgets (law)

```
                    ┌─────────────────────┐
                    │  SessionOrchestrator │
                    │  (HTTP / SSE entry)  │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                                 ▼
     ┌─────────────────┐              ┌─────────────────┐
     │  Dialogue graph │              │  Generate graph │
     │  CHEAP / often  │              │  EXPENSIVE once │
     │  may interrupt  │              │  abortable      │
     └─────────────────┘              └─────────────────┘
```

- **Dialogue:** every user message until scope + prefs are enough (and HITL waits).
- **Generate / replan:** only on explicit “build / update plan” (or equivalent), never on every chat turn.
- **Explore / booking:** separate HTTP flows; do not dump their tools into the dialogue graph.

### 5.2 Recommended graphs (not one mega-agent)

| Graph | Role | LLM? |
|-------|------|------|
| `dialogue_graph` | Intent → geo candidates → HITL → explain TripScope | Yes (bounded) |
| `generate_graph` | Catalog → retrieve → **engine** → validate → narrative → persist | LLM only for narrative (+ light prefs); engine is code |
| `revise_graph` (P6) | Patch prefs / day constraints → re-enter generate with caps | Yes + code |
| Explore / booking | **Not** LangGraph-first; plain services; optional later “assist” agent | Later |

### 5.3 Shared session state (conceptual)

Persist across turns (DB + optional checkpoint):

```text
TripSessionState
├── session_id, user_id? (guest cookie)
├── messages[]                  # chat transcript
├── budget: dialogue | generate | revise
├── intent                      # duration, vibe, constraints (structured)
├── trip_scope?
│     kind: city | region | country
│     geo_id, name, bbox / hubs[]
│     day_budget
├── hitl?
│     kind, candidates[], status: pending|resolved
├── catalog?
│     ready: bool, place_ids[], quality_notes
├── itinerary?                  # structured days/stops (engine output)
├── validation?                 # pass/fail + errors
├── trip_id?                    # after successful persist
├── run?
│     status, started_at, abort_requested
└── obs_trace_id
```

**LangGraph checkpoint:** useful for HITL interrupt (`interrupt` / wait for user choice) and resume. Prefer checkpointing **session planning state**, not raw tool spam.

### 5.4 Tools by phase (typed, phase-gated)

Only register tools that the current phase needs.

#### Dialogue tools (P2+)

| Tool / node | Type | Notes |
|-------------|------|--------|
| `parse_intent` | LLM structured out | Not necessarily a “tool”; schema-first |
| `geocode_search` | Tool → geo gateway | Returns candidates, never silent pick |
| `classify_scope` | Code (+ optional LLM hubs) | Geo metadata first; model second |
| `request_hitl` | Graph interrupt | Candidates / region chips in chat |
| `confirm_scope` | Code | Writes `trip_scope` |

#### Generate tools / nodes (P3–P4)

| Node | Type | Notes |
|------|------|--------|
| `acquire_catalog` | Tool/service | Region/hubs only — no country-centroid scrape |
| `retrieve_places` | Service | Geo/SQL first; vector later if available |
| `plan_itinerary` | **Pure code** | Travel engine — not LLM prose |
| `validate_itinerary` | **Pure code** | Gate before save |
| `write_narrative` | LLM | Titles/stories only |
| `persist_trip` | Code | Only if validation passed |

#### Explicitly not tools in dialogue

- Media fetch, booking search, nearby explore, PDF render.

### 5.5 State machine (happy path)

```
idle
  → dialogue
      → hitl_wait ──(user picks)──→ dialogue
      → scope_ready
  → generate_running ──(abort)──→ dialogue / cancelled
      → validating
          → fail → dialogue (honest + eval record)
          → pass → narrating → saved
  → revise (capped) → generate_running
```

### 5.6 Open LangGraph questions (still discussing)

1. Single compiled graph with conditional edges vs **two graphs** invoked by orchestrator? (**Lean: two graphs**, simpler budgets.)
2. HITL via LangGraph `interrupt` vs app-level “pending_hitl” row + next message? (Both work; interrupt is nicer UX if checkpointing is solid.)
3. How much of Wandr `travel_engine` purity do we reimplement vs simplified v1 engine?
4. Model choice via LiteLLM only — which default free/cheap model for dialogue vs narrative?

---

## 6. Empty vector strategy (recommendation)

**Recommendation: do not run Qdrant as a hard dependency until catalog content exists.**

| Phase | Retrieve strategy |
|-------|-------------------|
| P0–P2 | No retrieve |
| P3 catalog | Ingest POIs into **Postgres/PostGIS**; retrieve by bbox, category, tags, simple text |
| P4 planner | Same SQL/geo retrieve |
| Later | Add **Qdrant** (or pgvector) when places have enrich text; hybrid: geo filter → vector rank |
| Always | If vector empty or down: **geo fallback**; if still empty: honest HITL (bible failure table) |

**Why**

- Empty Qdrant adds ops cost and fake confidence.
- Meghalaya/Japan goldens need **correct geography** first, not embeddings.
- Facades stay the same: `retrieve_places(scope, prefs)` can swap internals.

**When to introduce vectors**

- Enough places per hub/region with summaries/tags
- Eval shows keyword/geo ranking is weak for vibe queries (“slow food”, “trek”)
- Then: Docker `qdrant` service + `qdrant-client` + embed via LiteLLM embeddings

---

## 7. Guidebook vs booking placeholder

### Guidebook (v1 target shape — from Meghalaya PDF)

- Cover: title, tags, dates, stats (days / hubs / legs)
- Hub sequence (e.g. Shillong → Cherrapunji → Shillong)
- Per leg: transfer summary, nights, narrative, **real** POIs (+ restaurants when in catalog)
- Map: stops always; polylines when routing exists
- Media: after generate (facade), not on hot path

### Booking slot (architecture only in v1)

```
TripArtifact
├── days[], stops[], narratives, map
└── booking: { status: "placeholder", stays: [], flights: [], activities: [] }
```

UI may show empty “Stays / Flights — coming later”. No fake prices. Future agentic booking scrolls options keyed off **saved trip** location; user can skip entirely.

---

## 8. Eval goldens (extended)

Keep bible cases, plus:

| Case | Expect |
|------|--------|
| **Meghalaya, ~4 days, trek/nature** | Region (or country→best region) multi-hub; compact East Khasi–style loop; no India-wide hop; no invented bridges/coords |
| **Japan, 3 days** | Single best region; named in chat |
| **Japan, 10 days, slow** | Hub sequence fitting days or HITL |
| **Kyoto, 4 days, food** | City wins |
| **Paris** ambiguous | HITL |
| Border / country filter | No foreign POIs |
| Missing duration | Ask; no persist |
| Abandoned generate | Abort; no unbounded spend |

---

## 9. Phased build (one done → next)

Proof = runnable check before unlocking the next phase.

| Phase | Ships | Proof |
|-------|--------|--------|
| **P0** | Repo layout, settings, health, obs skeleton, Docker API+DB | `GET /health` |
| **P1** | Chat session, streaming, guest cookie | Round-trip message |
| **P2** | Intent + TripScope + HITL + dialogue graph | Goldens: city/region/country/ambiguous (+ Meghalaya intent→scope) |
| **P3** | Catalog acquire by region/hubs | Honest readiness; PostGIS places |
| **P4** | Generate graph + engine + validate + persist | Itinerary; no invented coords |
| **P5** | Map + guidebook UI (+ print/PDF later) | Reopenable artifact |
| **P6** | Revision (capped replan) | Structure+map update |
| **P7** | Explore dual-tab | No fake POIs; last-trip locked pre-save |
| **P8** | Booking placeholder UI/API | Save without vendor |
| **P9** | Evals, cost caps, abort harden, rate limits | Golden harness pass |
| **Later** | Media enrich, Qdrant, agentic booking adapters | Facades only |

---

## 10. Still open (discuss before finalize)

1. **HITL mechanism:** LangGraph interrupt vs DB pending state?
2. **Travel engine depth in P4:** full optimizer vs greedy day packer?
3. **Default LLM models** (dialogue vs narrative) via LiteLLM?
4. **Auth:** guest cookie only until when for OAuth?
5. **PDF timing:** after P5 UI, or defer until media exists?
6. **pgvector vs Qdrant** when vectors arrive?
7. **Promote this draft** → update bible §Architecture + OpenSpec design change?

---

## 11. Change log (draft)

| Date | Change |
|------|--------|
| 2026-09-11 | Initial draft from /opsx-explore: locked L1–L9, packages, LangGraph sketch, empty-vector strategy, dual goldens, phased proofs |
