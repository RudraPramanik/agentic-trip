# Architecture draft — agentic-trip

> **Status:** SETTLED (promoted) — architecture + stack decisions locked for implementation planning.  
> **SSOT product behavior:** [`product-goal.md`](./product-goal.md)  
> **LLD (modules, APIs, algorithms):** [`llm.md`](./llm.md)  
> **Free media/map notes:** [`free-media-map-guidebook.md`](./free-media-map-guidebook.md)  
> **Rule:** Prefer changing this file + [`product-goal.md`](./product-goal.md) together if a locked decision shifts. OpenSpec implementation changes come next (phase-by-phase). HTTP paths for this product live in `llm.md` (`/api/v1/…` plus `GET /health` / `GET /health/ready`) — not Wandr.

Last updated: 2026-09-11 (product-goal SSOT rename + pointer retarget)

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
| L13 | **PDF** = **one phase after** guidebook UI; architect export DTO early | FE print/react-pdf; optional ARQ later; see §7 |
| L14 | **SWE shape** = feature modules + service protocols/ABCs + repositories | Smooth later CRUD/provider swaps; see §12 |
| L15 | **AI eng from early** = tracing + offline goldens skeleton in P0; deepen each phase | Langfuse-class traces; retrieval + agent spans; see §13 |
| L16 | **Multi-model via `LlmGateway` + LiteLLM** | Role aliases (dialogue/narrative/embed); Bedrock / Gemini / OpenRouter / NIM swap by env; see §4.5 |
| L17 | **Generate runner** = in-process **SSE first**; same port, ARQ adapter later | Catalog acquire still ARQ (P3); see §5.9 |
| L18 | **Auth** = guest cookie for continue; **OAuth later** | **Save trip** + **save explore places** require authenticated user; v1 persist is **`draft` only** (no save API); last-trip locked until `saved`; see §4.6 |
| L19 | Abstractions ports everywhere practical | LLM, geo, media, retrieve, travel engine, generate runner, auth |
| L20 | **Repo layout:** BE is **repo root** (`/src`), not `/backend` | `/frontend` colocated for now; extractable later; see §3 |
| L21 | **`phase-slices/`** = per-phase implementation blueprints | Blueprint → validate/CI → next phase; see §14–§15 |
| L22 | **Fail-soft / error boundary in every block** | Absolute fallbacks; no silent hang/hallucinate; see §15 |
| L23 | Modular monolith with **service-separated modules** under `/src` | Max modularity without microservices day one |
| L24 | **`monitor/` + `evals/`** are first-class modules beside features | Skeleton in P0; deepen later (P9 gate) |

---

## 2. Product goal (working one-liner)

Guest chats a vibe or place → system HITLs scope → builds a **catalog-grounded multi-day trip** with map → user revises in chat → opens a **Layla-like guidebook** (booking slot empty until later). Explore is a parallel geo feed. Agentic booking is optional and trip-keyed after save.

---

## 3. Repo layout (settled)

Backend lives at **repo root** as the main module (`/src`). Frontend is `/frontend` (same repo for scope; can split later). Modular monolith: service-separated modules, not a `/backend` package folder.

```
agentic-trip/
├── src/                       # FastAPI modular monolith (root app)
│   ├── main.py
│   ├── api/                   # HTTP routers only
│   ├── core/                  # settings, logging, security
│   ├── db/                    # SQLAlchemy session/engine
│   ├── ports/                 # Protocol/ABC gateways (optional top-level)
│   ├── modules/               # service-separated features
│   │   ├── chat/
│   │   ├── geo/
│   │   ├── catalog/
│   │   ├── planner/
│   │   ├── trips/
│   │   ├── explore/
│   │   ├── media/
│   │   ├── booking/           # hollow placeholder
│   │   ├── llm/               # LiteLLM gateway only
│   │   ├── agents/            # LangGraph graphs + state
│   │   ├── auth/              # guest now; OAuth later
│   │   ├── monitor/           # tracing / Langfuse (skeleton early; deepen later)
│   │   └── evals/             # golden harness / scores (skeleton early; deepen later)
│   └── workers/               # ARQ tasks
├── alembic/                   # migrations at repo root
├── tests/                     # pytest (+ tests/evals goldens)
├── frontend/                  # Next.js (run separately; extractable later)
├── system-docs/               # bible + settled architecture
├── phase-slices/              # per-phase blueprints, guardrails, validation
├── openspec/
├── docker-compose.yml         # api + db (+ redis/worker when needed)
├── Dockerfile                 # API image
├── pyproject.toml
└── README.md
```

**Why root `/src`:** single deployable API module; clearer imports; FE stays optional roommate until isolation.

**Modularity rule:** each `modules/<feature>/` owns service + repo/adapters for that concern; routers only depend on services; agents only call ports/services.

**AI eng modules:** `monitor/` (online traces/spans) and `evals/` (offline goldens/scores) sit beside other feature modules. P0 may only ship importable shells + fail-soft no-ops; deepen per phase (especially P9).

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

### 4.5 Multi-model LLM gateway (LiteLLM)

**Law:** no Bedrock/Gemini/OpenRouter/NIM SDKs in routers, agents, or services — only `LlmGateway`.

```
Services / graphs
       │
       ▼
 LlmGateway.complete(role, messages, …)
 LlmGateway.embed(texts)                 # later
       │
       ▼
 LiteLLM  ──env──▶  bedrock | gemini | openrouter | nvidia_nim | …
```

| Role alias (config) | Typical use | Switch by env |
|---------------------|-------------|----------------|
| `dialogue` | Intent parse, HITL copy, scope explain | e.g. OpenRouter / NIM free |
| `narrative` | Trip/day stories, titles | e.g. Bedrock when quality matters |
| `embed` | Vectors later | e.g. one cheap embed model |

Example env shape (illustrative):

```bash
LLM_DIALOGUE_MODEL=openrouter/meta-llama/...
LLM_NARRATIVE_MODEL=bedrock/anthropic.claude-...
LLM_EMBED_MODEL=openai/text-embedding-3-small   # or NIM/OpenRouter equivalent
# provider keys as required by LiteLLM
```

**Concurrent models:** different **roles** may point at different providers at once (dialogue on free, narrative on Bedrock). Do not fan out 2–3 models for the *same* call unless an explicit ensemble feature is designed later.

**Tracing:** every gateway call emits a generation span (model id, role, tokens, latency).

### 4.6 Auth & save rules

| Actor | Can |
|-------|-----|
| **Guest** (cookie) | Start chat, HITL, generate, view session draft trip + map, use Explore **Near me** |
| **Authenticated** (OAuth **later**) | **Save trip** (durable reopen), **save/bookmark explore places**, own **Last trip** Explore tab |

- No login wall on first prompt.
- Guest **continues** without forced signup; save actions prompt auth when OAuth exists.
- Until OAuth ships: keep `AuthPort` + guest identity; optional stub “dev user” only in local if needed — do not fake OAuth in prod paths.
- **v1 (P0–P9):** generate persists a **`draft`** reopenable in the guest cookie session. That is not a saved trip. **Do not add a save API** in these phases. Last-trip stays locked. Tests for the `saved` branch use a fixture row only — not a fake OAuth user on prod paths.
- **Last trip location** Explore still requires a **saved** trip (bible) ⇒ locked through P0–P9; effectively authenticated once Later save exists.

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

**LangGraph checkpoint:** Postgres-backed checkpointer for dialogue HITL interrupt/resume. Checkpoint **session planning state**, not raw tool spam. Redis is for ARQ/queues, not the only HITL source of truth.

### 5.4 Tools by phase (typed, phase-gated)

Only register tools that the current phase needs.

#### Dialogue tools (P2+)

| Tool / node | Type | Notes |
|-------------|------|--------|
| `parse_intent` | LLM structured out | Not necessarily a "tool"; schema-first |
| `geocode_search` | Tool → geo gateway | Returns candidates, never silent pick |
| `classify_scope` | Code (+ optional LLM hubs) | Geo metadata first; model second |
| `request_hitl` | Graph **interrupt** | Candidates / region chips in chat |
| `confirm_scope` | Code | Writes `trip_scope` |

#### Generate tools / nodes (P3–P4)

| Node | Type | Notes |
|------|------|--------|
| `acquire_catalog` | Service / ARQ job | Region/hubs only — no country-centroid scrape |
| `retrieve_places` | Service | Geo/SQL first; vector later if available |
| `plan_itinerary` | **Pure code** | Constrained greedy packer (§5.7) |
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

### 5.6 HITL — settled recommendation

**Prefer: LangGraph `interrupt` + Postgres checkpointer**, with a **thin session projection** for the UI.

```
┌──────────────┐   interrupt    ┌─────────────┐
│ dialogue     │───────────────▶│ hitl_wait   │
│ graph        │                │ checkpoint  │
└──────────────┘                └──────┬──────┘
                                       │ user picks chip / replies
                                       ▼
                                resume + confirm_scope
```

| Piece | Responsibility |
|-------|----------------|
| LangGraph interrupt | Canonical pause; state control you want |
| Postgres checkpointer | Survive API restart; guest session resume |
| `TripSessionState.hitl` in DB/API | FE chips, "waiting on you", analytics |
| User's next chat message / chip POST | Resume token + choice → graph continues |

**Why this fits our limits**

- Product HITL is **in-chat** and multi-turn — graph interrupt matches that better than a one-off form page.
- Modular monolith + guest cookies → durable checkpoint in **Postgres** (already required), not Redis-only.
- You already want LangGraph for state — use it for the hard pause; don't maintain a second parallel state machine.

**What HITL is not**

- Not an ARQ job.
- Not used for generate abort (that's `abort_requested` + cancel stream/worker).
- Not a separate search-first site.

**Fallback if interrupt proves painful in P2:** keep the same `hitl` projection and resume API; demote graph to "stateless nodes + DB pending" without changing the product contract. Specs stay the same.

### 5.7 P4 travel engine depth — settled recommendation

**v1 = constrained greedy day-packer + hard validate gate** (market-honest, map-trustable), not a full mathematical optimizer.

| Responsibility | v1 behavior |
|----------------|-------------|
| Inputs | `trip_scope`, day_budget, retrieved place ids + coords + categories, prefs |
| Pack | Assign stops to days under time/walk/transfer caps; respect hub sequence for region trips |
| Travel times | Fail-soft matrix (OSRM/table or haversine+penalty); **no fake polylines** |
| Output | Ordered days/stops with real place ids |
| Validate | Day caps, catalog grounding, country filter, transfer sanity |
| LLM | **Forbidden** for stop invention / coords / order |

**Upgrade path (only if evals demand it):** better scoring, 2-opt local search, or OR-Tools — behind the same `TravelEngine` protocol.

**Why not full optimizer on day one:** Meghalaya/Japan goldens fail first on **wrong scope / empty catalog / invented POIs**, not on 3% suboptimal walk order. Ship purity + evals, then deepen.

### 5.8 Generate execution — settled (product + logic)

**Recommendation: P4 = in-process generate + SSE progress; ARQ behind the same `GenerateRunner` port later.**

| Concern | Product need | Choice |
|---------|--------------|--------|
| User sees progress | “Acquiring places… planning day 2… writing story…” | SSE/event stream |
| User leaves | Stop spend | Abort on disconnect + `abort_requested` |
| Long catalog scrape | Don’t block API workers forever | **ARQ from P3** for `acquire_catalog` |
| Trip shape unproven | Avoid two failure domains (API + worker) on day one of generate | In-process generate first |
| Scale later | Same UX, different executor | `GENERATE_EXECUTOR=inprocess\|arq` |

```
API ──SSE──▶ GenerateRunner.start(session_id)
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
 InProcessRunner          ArqGenerateRunner (later)
 (P4 default)             enqueue + progress bus
        │                       │
        └───────────┬───────────┘
                    ▼
            GenerateService / generate_graph
            (identical domain logic)
```

**Why not ARQ-for-generate on day one:** catalog already async; generate needs tight abort + streaming narrative; proving itinerary quality matters more than worker topology. When timeouts/multi-instance hurt, flip the adapter — **not** a rewrite.

### 5.9 Still open (agents) — minor

1. Exact default model IDs per role (env values; not architecture).
2. How closely to mirror Wandr travel_engine APIs vs a smaller new `TravelEngine` interface (lean smaller).

---

## 6. Empty vector strategy (recommendation)

**Day one: PostGIS only. Later vectors: prefer Qdrant** (your prior apps + Docker isolation). **pgvector remains a valid alternative** if we want fewer moving parts.

| Phase | Retrieve strategy |
|-------|-------------------|
| P0–P2 | No retrieve |
| P3 catalog | Ingest POIs into **Postgres/PostGIS**; retrieve by bbox, category, tags, simple text |
| P4 planner | Same SQL/geo retrieve |
| Later | **Qdrant** hybrid: geo filter → vector rank (embed via LiteLLM) |
| Always | If vector empty or down: **geo fallback**; if still empty: honest HITL |

**Qdrant vs pgvector (when the time comes)**

| | Qdrant | pgvector |
|--|--------|----------|
| Fit | Dedicated ANN, filters, your existing skill | One less service; SQL joins |
| Ops | Extra Docker service | Extension on PostGIS box |
| **Default for this product** | **Yes, when vectors start** | Keep as spike option |

Facade stays `retrieve_places(scope, prefs)` either way.

---

## 7. Guidebook vs booking placeholder vs PDF

### Guidebook (v1 target shape — from Meghalaya PDF)

- Cover: title, tags, dates, stats (days / hubs / legs)
- Hub sequence (e.g. Shillong → Cherrapunji → Shillong)
- Per leg: transfer summary, nights, narrative, **real** POIs (+ restaurants when in catalog)
- Map: stops always; polylines when routing exists
- Media: after generate (facade), not on hot path
- Booking block: **empty placeholder**

### Booking slot (architecture only in v1)

```
TripArtifact
├── days[], stops[], narratives, map
└── booking: { status: "placeholder", stays: [], flights: [], activities: [] }
```

### PDF export (architect now, ship one phase later)

| Layer | Role |
|-------|------|
| **Source of truth** | Saved structured trip (never LLM-written PDF as plan) |
| **P5** | Guidebook **UI** + stable **`GuidebookExport` DTO** (JSON shape = PDF input) |
| **P5b / after P5** | FE print CSS and/or `@react-pdf/renderer` consuming that DTO |
| **Optional later** | ARQ `render_pdf(trip_id)` for email/files |
| **Not** | A free-form "PDF agent" inventing hotels/prices |

**Ease later:** P5 builds guidebook from the same export view-model the PDF will use — no second narrative pipeline.

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
| **P0** | Repo layout, settings, health, **obs/eval skeleton**, Docker API+DB | `GET /health` + empty trace/eval smoke |
| **P1** | Chat session, streaming, guest cookie | Round-trip message (traced) |
| **P2** | Intent + TripScope + **HITL interrupt** + dialogue graph | Goldens: city/region/country/ambiguous (+ Meghalaya intent→scope) |
| **P3** | Catalog acquire (ARQ) by region/hubs | Honest readiness; PostGIS places; retrieve spans |
| **P4** | Generate graph + greedy engine + validate + **SSE** (`GenerateRunner` in-process) | Itinerary; no invented coords; abort works |
| **P5** | Map + guidebook UI + **export DTO** (no PDF yet) | Reopenable artifact |
| **P5b** | PDF/print export from export DTO | Download/print guidebook |
| **P6** | Revision (capped replan) | Structure+map update |
| **P7** | Explore dual-tab | No fake POIs; last-trip locked pre-save |
| **P8** | Booking placeholder UI/API | Save without vendor |
| **P9** | Eval gate harden, cost caps, abort, rate limits | Golden harness pass in CI |
| **Later** | OAuth, media enrich, Qdrant, ARQ generate adapter, agentic booking | Facades only |

---

## 10. Open items (non-blocking)

1. Concrete LiteLLM model id strings per role (ops/env).
2. Exact OAuth provider when auth phase starts.
3. Optional OpenSpec change per phase vs one umbrella “foundation” change — see §14.

---

## 11. Change log

| Date | Change |
|------|--------|
| 2026-09-11 | Initial draft: L1–L9 |
| 2026-09-11 | L10–L15: HITL, engine, ARQ, Qdrant-later, PDF/FE, SWE, evals |
| 2026-09-11 | **Promoted:** L16–L19 multi-model, SSE generate runner, guest/save auth, PDF as P5b; §14 impl procedure |

---

## 12. SWE architecture — features, services, OOP

Goal: later provider swaps and CRUD stay boring.

```
api (routers)  →  application services  →  domain ports (Protocol/ABC)
                         │                         │
                         ▼                         ▼
                   repositories              adapters (geo, llm, media, qdrant…)
                         │
                         ▼
                      Postgres
```

| Layer | Rule |
|-------|------|
| **Routers** | HTTP only; no business logic; no vendor SDKs |
| **Services** | Use-cases (`ChatService`, `CatalogService`, `TripService`) |
| **Ports** | `GeoGateway`, `LlmGateway`, `PlaceRepository`, `TravelEngine`, `MediaProvider`, `RetrievePlaces`, `GenerateRunner`, `AuthPort` |
| **Adapters** | Nominatim, Overpass, LiteLLM, Qdrant, ARQ enqueue |
| **Agents** | Call ports/services; graphs do not own SQL or httpx to vendors directly |
| **DTOs** | Pydantic at edges; domain models inward |

**Patterns we want:** dependency injection via FastAPI `Depends` / constructors; one gateway per concern (LLM, geo, media); fail-soft adapters return empty/errors, never hang; feature folders mirror modules.

**Anti-patterns:** LLM SDK in routers; inventing coords in adapters "to look nice"; God-service that mixes chat + booking + PDF.

---

## 13. AI engineering — tracing & evals (from early)

Market-standard loop you can reuse for client work:

```
Instrument → Trace every generate/retrieve → Offline goldens → Score → Regress in CI
                │
                └── Online: sample traces, cost, latency, abort rate
```

### Concepts (skills to practice on this repo)

| Concept | Meaning here |
|---------|----------------|
| **Trace** | One user turn or one generate run |
| **Span** | Nested step: `geocode`, `retrieve`, `plan`, `validate`, `narrative` |
| **Generation** | LLM call (model, tokens, latency, prompt/output redacted as needed) |
| **Retrieval span** | Query, filters, ids returned, latency, empty? |
| **Score** | Automated or LLM-as-judge or human label on a trace |
| **Dataset / goldens** | Fixed cases (Meghalaya, Japan, …) with expected asserts |
| **Offline eval** | Run goldens in CI/worker; fail build on regressions |
| **Online eval** | Sample live traces; dashboards (Langfuse) |

### What we put in **P0** (skeleton, not perfection)

- Langfuse (or equivalent) client wired behind `obs` module; no-op if keys missing (**fail-soft**)
- Trace id on session/generate
- Empty golden runner that can assert health / smoke
- Doc: how to add a span

### What we add **per phase**

| Phase | Must emit |
|-------|-----------|
| P1 | Chat turn traces |
| P2 | Intent + HITL + scope spans; golden scope asserts |
| P3 | Acquire + **retrieve** spans (even SQL retrieve) |
| P4 | Plan/validate/narrative; "no invented place id" asserts |
| P9 | CI gate + cost caps |

### Eval asserts (examples)

- Scope kind matches golden
- Every scheduled stop id ∈ retrieved catalog
- No foreign-country POI
- Validation fail ⇒ no successful persist
- Abort ⇒ no unbounded continuation

**Career note:** Shipping this loop on a real product (traces + retrieval spans + golden CI) is stronger portfolio evidence than toy ReAct demos.

---

## 14. Implementation procedure (phase-slices program)

```
blueprint.md  P{n}.1 → P{n}.2 → …  →  tests + CI validation gate  →  P{n+1}
       │                                    │
       ├──── llm.md (LLD: services/routes) ─┤
       └──── fail-soft + SWE/LLD rules ─────┘
```

Sub-phases live **inside** existing `phase-slices/<id>/blueprint.md` (e.g. P0.1 … P0.12). Do not create nested `p0.1/` folders. A later OpenSpec **code** change remains one per phase (`p0-foundation`, …) and is executed sub-phase-by-sub-phase.

HTTP for this product: see [`llm.md`](./llm.md) §5 (`GET /health`, `GET /health/ready`, `/api/v1/…`). Do not invent Wandr `guideagent` paths.

### Relationship: OpenSpec vs phase-slices

| Layer | Role |
|-------|------|
| **`phase-slices/Pn/`** | Sub-phase blueprint, guardrails (fail-soft + SWE/LLD), validation, refs |
| **`system-docs/llm.md`** | Low-level design SSOT (classes, APIs, algorithms, sequences) |
| **OpenSpec change `pN-…`** | Formal proposal/design/tasks/specs when that phase is built |
| **`phase-slices-program`** | Docs change that locked layout + authored slice shells |
| **`phase-slices-function-level-lld`** | Docs change that split slices into function-level sub-phases + LLD |

### P0 foundation (first code slice — later apply)

Execute as **P0.1 → P0.12** in [`phase-slices/p0-foundation/blueprint.md`](./phase-slices/p0-foundation/blueprint.md):

1. P0.1–P0.3: `/src` package, settings/logging, Compose `api`+`db`, Alembic.
2. P0.4–P0.9: ports stubs, module shells, guest AuthPort, LlmGateway stub, monitor no-op, evals smoke.
3. P0.10: `GET /health` + `GET /health/ready` + `main.py`.
4. P0.11–P0.12: `workers/` placeholder; pytest + CI smoke.
5. Phase proof: health + pytest smoke + CI job green. Do not start P1 until the P0 validation gate passes.

### Guardrails while implementing

- One **sub-phase** proof before the next sub-phase; one **phase** proof before the next slice.
- No vendor SDKs outside adapters.
- No media/PDF on generate hot path.
- Guest can continue; durable save waits for auth capability.
- Every external/IO block documents **failure → fallback** (bible table + slice guardrails).
- SWE/LLD regulations: [`phase-slices/SHARED-SWE-LLD.md`](./phase-slices/SHARED-SWE-LLD.md).
- Prefer `/opsx-propose` + `/opsx-apply` **per phase** for code; follow `llm.md` for function/route names.

---

## 15. Fail-soft law + phase-slice package shape

### Fail-soft (absolute)

Borrowed from the product bible; enforced per module/block:

| Kind | On failure | Never |
|------|------------|--------|
| Geocoder | HITL / ask | Silent country centroid |
| Catalog / retrieve | Honest empty + HITL | Invent POIs or foreign fill |
| LLM | Defaults / wrap-up | Invent coords or stop order |
| Routing | Points only / soft times | Fake polylines |
| GPS/IP | Approximate copy or empty Near me | Fake city / fill last-trip |
| Worker / ARQ | Retry + marked failed | Hang forever |
| Obs / Langfuse | No-op | Crash the request |
| Auth save | Prompt login later | Corrupt guest into fake user |

**Code shape:** adapters return empty/error results; services map to user-visible honest outcomes; agents respect tool budgets and abort.

### Each `phase-slices/<id>/` package

| File | Contents |
|------|----------|
| `blueprint.md` | Goal, scope, numbered sub-phases (`P{n}.{m}`) with services/routes/functions, slice proof |
| `guardrails.md` | Fail-soft table + SWE/LLD delta for this slice |
| `validation.md` | Sub-phase checks + phase CI; all must pass before next slice |
| `references.md` | Links to bible, architecture, `llm.md`, OpenSpec specs, shared rules |

Shared: [`phase-slices/SHARED-FAIL-SOFT.md`](./phase-slices/SHARED-FAIL-SOFT.md), [`phase-slices/SHARED-SWE-LLD.md`](./phase-slices/SHARED-SWE-LLD.md), [`llm.md`](./llm.md).

### Slice catalog

| ID | Name |
|----|------|
| `p0-foundation` | Root `/src`, Docker, health, **monitor** + **evals** shells |
| `p1-chat` | Guest cookie, chat SSE |
| `p2-dialogue-scope` | Intent, TripScope, HITL interrupt |
| `p3-catalog` | Acquire ARQ, PostGIS retrieve |
| `p4-generate` | GenerateRunner SSE, engine, validate, persist draft |
| `p5-guidebook-map` | Map + guidebook UI + export DTO |
| `p5b-pdf-export` | PDF/print from export DTO |
| `p6-revision` | Capped replan |
| `p7-explore` | Near me + last-trip |
| `p8-booking-placeholder` | Hollow stays slot |
| `p9-hardening` | CI eval gate, cost caps, abort harden |

---

## 16. Change log

| Date | Change |
|------|--------|
| 2026-09-11 | Initial draft: L1–L9 |
| 2026-09-11 | L10–L15: HITL, engine, ARQ, Qdrant-later, PDF/FE, SWE, evals |
| 2026-09-11 | Promoted: L16–L19 multi-model, SSE generate, guest/save, PDF P5b |
| 2026-09-11 | L20–L23: root `/src`, phase-slices, fail-soft, service modules; §15 |
| 2026-09-11 | **Apply `phase-slices-program`:** all slice packages + shared fail-soft; L24 `monitor/`+`evals/` modules; ready to archive |
| 2026-09-11 | **Apply `phase-slices-function-level-lld`:** sub-phases inside blueprints; `llm.md` LLD; SWE/LLD guardrails; HTTP catalog `/api/v1` |
| 2026-09-11 | Product behavior SSOT renamed to [`product-goal.md`](./product-goal.md) (was `chat-first-trip-os.md`); pointers retargeted |
