## Why

P2 shipped durable `trip_scope` (city/region/country + hubs) after dialogue HITL, but generate still has no grounded POI catalog: no PostGIS places, no Overpass/OTM acquire, no bbox retrieve, and no readiness/job status. Without P3, packing and validation cannot bind stops to real place ids. P2 is done; P3 is the next product proof.

Work type: **backend + infra + tests** (cross-cutting within the P3 slice). Optional thin FE readiness surface only if needed to exercise acquire; no generate CTA. Not docs-only.

## What Changes

- Persist `Place` rows with PostGIS geometry and a GiST index; implement `PlaceRepository.upsert_many` + `retrieve(scope, prefs)`.
- Add places adapters behind a facade (`OverpassAdapter`, `OtmAdapter` → `PlacesFacade.fetch_for_scope`).
- Implement `CatalogService.acquire` / `readiness` / `retrieve` with typed `AcquireResult` (`ready` | `partial` | `failed`) and `RetrieveResult`.
- Add ARQ worker job `acquire_catalog` with bounded retry; Compose `redis` + `worker` services (API still boots without Redis for health).
- Expose product catalog HTTP: `GET /api/v1/sessions/{id}/catalog`, `POST /api/v1/catalog/acquire`.
- Emit observability retrieve spans (or no-op when unconfigured).
- Country filter on ingest and retrieve; region/hub polygons only — never country-centroid scrape or foreign refill.
- Proof tests per `system-docs/phase-slices/p3-catalog/validation.md` (acquire success/fail, country filter, honest empty retrieve, ASGI catalog routes).
- Follow `system-docs/phase-slices/p3-catalog/` (P3.1–P3.8, guardrails, validation), `system-docs/llm.md` §7.3 / §8, `SHARED-SWE-LLD.md`, and `SHARED-FAIL-SOFT.md`.

**Non-goals:** generate / Build plan CTA / packing (P4); itinerary persist; Qdrant / vector index; map/guidebook; Explore; booking; Wandr paths/DTOs/env; hallucinated coords/POIs/polylines; country-centroid radius scrape; unbounded ARQ hang.

**BREAKING:** none for external clients beyond additive catalog routes. **Spec-level:** `api-foundation` gains catalog product routes for this slice; generate/trip/explore/booking remain forbidden until their slices.

## Capabilities

### New Capabilities

- `catalog-acquire-retrieve`: Place persistence (PostGIS + GiST), places facade acquire for session scope (region/hubs only), ARQ bounded acquire job, readiness projection, PostGIS bbox/category/tags retrieve with country filter, catalog HTTP, and retrieve observability spans.

### Modified Capabilities

- `api-foundation`: Allow `GET /api/v1/sessions/{id}/catalog` and `POST /api/v1/catalog/acquire` as product routes once this slice ships; keep generate/trip/explore/booking non-product; clarify Redis/worker are required for acquire jobs but not for API liveness.
- `fail-soft-boundaries`: Tighten P3 catalog acquire/retrieve/worker fallbacks — Overpass/OTM down → empty/partial + honest readiness; thin catalog → no foreign/centroid fill; ARQ/Redis down → marked failed + user-visible status; empty retrieve → honest empty (HITL deferred to generate); retrieve geo-fallback language clarified as PostGIS-only in v1.
- `adaptive-country-scope`: Reinforce country filter on catalog ingest and retrieve (not only scheduled stops); unknown-country border POIs excluded at upsert/retrieve.
- `guest-chat-sessions`: Session projection MAY surface catalog readiness/`catalog` JSON when acquire has run; chat and HITL resume MUST still NOT start acquire or generate.

## Impact

- **Code / APIs:** `src/modules/catalog/` (models, repository, adapters, service), `src/workers/acquire.py`, `src/api/catalog.py`, `PlaceRepository` port methods, session `catalog` JSONB readiness fields, composition root + worker entry wiring.
- **Infra:** Compose `redis` + `worker`; ARQ settings; Alembic places migration (PostGIS geometry + GiST + country code).
- **Frontend:** optional thin readiness/status if needed to prove acquire UX; no Build plan / generate.
- **Tests / CI:** unit + ASGI proofs for P3.1–P3.8; mock Overpass/OTM; acquire success/fail; country filter; empty retrieve; retrieve span/no-op; CI blocks on failure. Prefer fakes behind ports (no live Overpass required for green CI).
- **Docs:** implement against existing `system-docs/phase-slices/p3-catalog/`; if blueprint and `llm.md` disagree, resolve both in this change (no third shape).
- **Deps:** ARQ + Redis; httpx for Overpass/OTM; existing FastAPI/SQLAlchemy/PostGIS/ObsPort stack.
