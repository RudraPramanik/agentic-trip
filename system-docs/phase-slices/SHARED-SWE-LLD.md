# Shared SWE / LLD regulations

> Low-level design SSOT: [`../llm.md`](../llm.md)  
> Fail-soft (product): [`SHARED-FAIL-SOFT.md`](./SHARED-FAIL-SOFT.md)  
> Architecture: [`../architecture-draft.md`](../architecture-draft.md) §12  
> Product bible: [`../product-goal.md`](../product-goal.md)

Copy slice-specific deltas into each `guardrails.md`. Do not invent Wandr paths, DTOs, or env vars.

## 1. Layering (call chain)

```
api routers  →  application services  →  ports (Protocol/ABC)  →  adapters | repositories
```

| Layer | May | Must not |
|-------|-----|----------|
| **Router** | HTTP parse/serialize, `Depends`, status codes | Business rules, vendor SDKs, SQL, LangGraph internals |
| **Service** | One use-case per method; orchestrate ports | Import LiteLLM/Nominatim/Overpass clients directly |
| **Port** | Stable Protocol/ABC | Provider-specific types |
| **Adapter** | Vendor HTTP, retries, mapping to domain | Invent coords/POIs/polylines |
| **Repository** | Persistence + queries | HTTP to vendors |
| **Agent/graph** | Call services/ports | SQL, vendor `httpx`, media/PDF/booking tools |

Composition root: `src/main.py` (and worker entry) wires adapters. Routers never construct vendors.

## 2. SWE architecture

- **Modular monolith:** feature folders under `src/modules/<feature>/`; no microservices in v1.
- **SOLID:** one reason to change per service; ports for LLM, geo, media, retrieve, engine, runner, auth, obs.
- **No God-service:** chat, catalog, generate, explore, booking, PDF stay separate services.
- **DI:** constructors / FastAPI `Depends`; test with fakes behind ports.
- **Idempotency:** acquire jobs and abort flags safe to retry; do not double-persist a successful trip from a replay without an idempotency key/status check.
- **Errors:** adapters return typed empty/error results; services map to honest user-visible outcomes; never hang.
- **DTOs vs domain:** Pydantic at HTTP edges; domain models inward; engine does not take HTTP DTOs as its inner type.
- **Tests:** unit (engine, validate, classify_scope); API (routers); goldens (dialogue/generate).

## 3. Naming consistency

| Kind | Pattern | Examples |
|------|---------|----------|
| Service | `*Service` | `ChatService`, `CatalogService`, `ExploreService` |
| Port | `*Port` / `*Gateway` | `AuthPort`, `LlmGateway`, `GeoGateway` |
| Repository | `*Repository` | `PlaceRepository`, `SessionRepository` |
| Adapter | `*Adapter` | `NominatimAdapter`, `LiteLlmAdapter` |
| Router | `*Router` / `api/*.py` | `chat_router` |
| DTO | `*Request` / `*Response` / `*Export` | `GuidebookExport` |

Python modules: `snake_case`. Types: `PascalCase`. Route functions: `verb_noun` (`create_session`, `send_message`).

## 4. System design constraints

- Single `LlmGateway`; single `GeoGateway` (bible).
- Dialogue budget vs generate budget; never generate on every chat turn.
- Phase-gated tools; bounded loops; validate before persist.
- Stream abort on disconnect; generate timeout.
- Guest cookie continue; durable save / last-trip require authenticated saved trip (OAuth later).
- Catalog ingest: chosen region/hubs only — never country-centroid scrape.
- Country filter: no foreign POIs on the schedule.
- Observability fail-soft: missing Langfuse keys must not crash requests.
- HTTP for this product lives under `/api/v1/` plus `GET /health` and `GET /health/ready`. Not Wandr `guideagent`.

## 5. Algorithm locks (v1)

| Concern | Algorithm | Forbidden |
|---------|-----------|-----------|
| Day packing | Constrained greedy packer + hard validate | LLM stop-order; OR-Tools unless behind `TravelEngine` later |
| Travel times | OSRM table if present else haversine + penalty | Fake polylines |
| Retrieve | PostGIS bbox + category/tags; GiST on geometry | Invent POIs; Qdrant required on day one |
| Geocode | Return candidates; HITL if ambiguous | Silent country centroid |
| Scope classify | Geo metadata first; LLM hubs only if thin country | Model as sole admin identity |
| Near me | GPS then IP; honest empty | Fake city; fill last-trip from IP |
| Catalog acquire | Bounded ARQ; region/hubs | Unbounded hang; foreign refill |
| Generate abort | Disconnect + `abort_requested` cooperative cancel | Continue spend after abort |

Complexity notes belong on the owning function (`pack_days`, `retrieve_places`, `haversine_meters`).

## 6. LLD patterns

- **Hexagonal / ports & adapters** for every external system.
- **Facade** for media and places (multiple free providers, one port).
- **Strategy** for `GenerateRunner` (`inprocess` now, `arq` later) and `TravelEngine`.
- **Repository** for sessions, places, trips.
- **Typed result objects** (`AcquireResult`, `RetrieveResult`, `ValidateResult`) instead of raising through HTTP accidentally.
- **Interrupt** (LangGraph) for HITL; not an ARQ job.
- **SSE progress bus** for generate; same domain graph regardless of runner adapter.

## 7. Anti-patterns (never)

- Vendor SDK in a router, graph node, or unrelated service.
- Invented coordinates, venues, or crow-flies polylines “to look nicer”.
- Unbounded ReAct / tool loops.
- Country-centroid radius scrape.
- LLM-authored day structure or stop order.
- Media fetch or PDF render on the generate hot path.
- Fake booking rates or vendor checkout in v1.
- Copying Wandr OpenAPI paths, DTOs, or env vars.

Slice authors: link this file from `references.md` and keep a short **SWE / LLD delta** in `guardrails.md`.
