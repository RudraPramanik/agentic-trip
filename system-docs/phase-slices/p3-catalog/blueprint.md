# P3 Catalog acquire + retrieve — blueprint

> Status: planning blueprint (implement via later OpenSpec `p3-catalog`).  
> LLD: [`../../llm.md`](../../llm.md) §7.3, §8

## Goal

Acquire POIs by region/hubs (ARQ); store PostGIS; retrieve by bbox/category/tags; retrieve spans in obs.

## Scope / modules

modules/catalog, workers acquire, geo places adapters (Overpass/OTM)

## Step plan

Implement **one sub-phase at a time**.

### P3.1 — Place model + PostGIS repo

- **Goal:** Persist places with geometry and GiST index.
- **Modules:** `src/modules/catalog/models.py`, `repository.py`
- **Types:** `Place`, `PlaceRepository`
- **Functions:** `upsert_many`, `retrieve(scope, prefs)`
- **Services:** none yet
- **Routes / APIs:** none
- **Algorithms / data:** GiST on geometry; country code column for filter
- **Depends on:** P0.3
- **Proof:** Alembic migration; upsert + bbox query in test
- **Non-goals:** vector index

### P3.2 — Places adapters

- **Goal:** Overpass/OTM behind a facade; map to `Place`.
- **Modules:** `src/modules/catalog/adapters/`
- **Types:** `PlacesFacade`, `OverpassAdapter`, `OtmAdapter`
- **Functions:** `fetch_for_scope(scope) -> list[Place]`
- **Services:** none
- **Routes / APIs:** none
- **Algorithms / data:** region/hub polygons only
- **Depends on:** P3.1
- **Proof:** mock HTTP → mapped places; down → empty/partial result type
- **Non-goals:** country-centroid scrape

### P3.3 — CatalogService.acquire

- **Goal:** Use-case: enqueue/run acquire for session scope.
- **Modules:** `src/modules/catalog/service.py`
- **Types:** `AcquireResult` (`ready` | `partial` | `failed`)
- **Functions:** `CatalogService.acquire(session_id)`, `readiness(session_id)`
- **Services:** `CatalogService`
- **Routes / APIs:** none yet
- **Algorithms / data:** uses `trip_scope` hubs/region; country filter on ingest
- **Depends on:** P3.2, P2.7
- **Proof:** unit: region scope → facade called with that bbox; country scope without hubs refused or HITL
- **Non-goals:** packing

### P3.4 — ARQ acquire_catalog

- **Goal:** Bounded background job + Redis worker.
- **Modules:** `src/workers/acquire.py`, compose `redis` + `worker`
- **Types:** ARQ job
- **Functions:** `acquire_catalog(ctx, session_id)`
- **Services:** `CatalogService` from worker
- **Routes / APIs:** none
- **Algorithms / data:** bounded retry → marked failed; no infinite hang
- **Depends on:** P3.3, P0.11
- **Proof:** job success + failure paths; user-visible failed status
- **Non-goals:** generate on worker

### P3.5 — retrieve_places

- **Goal:** In-scope retrieve by bbox/category/tags.
- **Modules:** `PlaceRepository.retrieve`
- **Types:** `RetrieveResult`
- **Functions:** `retrieve_places(scope, prefs)`
- **Services:** `CatalogService.retrieve`
- **Routes / APIs:** none
- **Algorithms / data:** PostGIS bbox ∩ filters; empty → typed empty (HITL later at generate)
- **Depends on:** P3.1
- **Proof:** returns real ids or honest empty; foreign country excluded
- **Non-goals:** Qdrant

### P3.6 — Catalog HTTP

- **Goal:** Readiness + acquire enqueue.
- **Modules:** `src/api/catalog.py`
- **Types:** readiness DTO
- **Functions:** router handlers
- **Services:** `CatalogService`
- **Routes / APIs:** `GET /api/v1/sessions/{id}/catalog`, `POST /api/v1/catalog/acquire`
- **Algorithms / data:** —
- **Depends on:** P3.3, P3.4
- **Proof:** ASGI enqueue + readiness payload
- **Non-goals:** Wandr paths

### P3.7 — Retrieve spans

- **Goal:** Obs retrieve span (query, filters, ids, empty?).
- **Modules:** `CatalogService.retrieve` + `ObsPort`
- **Types:** —
- **Functions:** span around retrieve
- **Services:** catalog + monitor
- **Routes / APIs:** none new
- **Algorithms / data:** —
- **Depends on:** P3.5, P0.8
- **Proof:** fake obs records retrieve span or no-op
- **Non-goals:** generate spans

### P3.8 — Proof tests

- **Goal:** Acquire readiness + retrieve honesty.
- **Modules:** `tests/`
- **Types:** —
- **Functions:** pytest acquire success/fail; country filter; empty retrieve
- **Services:** —
- **Routes / APIs:** P3 routes
- **Algorithms / data:** —
- **Depends on:** P3.6, P3.7
- **Proof:** acquire for a hub/region returns readiness; retrieve returns real place ids or honest empty
- **Non-goals:** itinerary persist

## Proof

Acquire for a hub/region returns readiness; retrieve returns real place ids or honest empty

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
