## 1. Place model + PostGIS repo (P3.1)

- [x] 1.1 backend: Add `Place` domain/ORM model (geometry, category/tags, country_code, provider ids) and Alembic migration with GiST on geometry
- [x] 1.2 backend: Implement `PlaceRepository.upsert_many` + `retrieve(scope, prefs)` (bbox ∩ filters + country); extend port; wire composition root
- [x] 1.3 backend: Proof — migration applies; upsert + bbox retrieve unit test; foreign/unknown-country excluded

## 2. Places adapters + facade (P3.2)

- [x] 2.1 backend: Add `OverpassAdapter` and `OtmAdapter` (httpx timeout → empty) mapping provider payloads to `Place`
- [x] 2.2 backend: Implement `PlacesFacade.fetch_for_scope(scope)` (region/hub polygons only; merge/dedupe; typed partial on provider failure)
- [x] 2.3 backend: Proof — mock HTTP → mapped places; provider down → empty/partial (no invented POIs)

## 3. CatalogService.acquire + readiness (P3.3)

- [x] 3.1 backend: Implement `CatalogService.acquire(session_id)` / `readiness(session_id)` with `AcquireResult` (`ready` | `partial` | `failed`); use `trip_scope` hubs/region; country filter on ingest
- [x] 3.2 backend: Refuse country-without-hubs (honest failed / needs hubs — no country-centroid scrape); write session `catalog` JSONB projection
- [x] 3.3 backend: Proof — unit: region/hub scope → facade called with that geography; country-without-hubs refused

## 4. ARQ acquire_catalog + Compose (P3.4)

- [x] 4.1 infra: Add Compose `redis` + `worker` services and ARQ settings; API still boots and `GET /health` without Redis
- [x] 4.2 backend: Implement `acquire_catalog(ctx, session_id)` worker calling `CatalogService`; bounded retry → mark `failed`; safe re-enqueue/idempotency
- [x] 4.3 backend: Wire enqueue from service/composition root; Redis/worker down → honest failed/enqueue error (no hang)
- [x] 4.4 backend: Proof — job success path updates readiness; failure path user-visible `failed`

## 5. retrieve_places (P3.5)

- [x] 5.1 backend: Implement `CatalogService.retrieve` → `RetrieveResult` (real ids or typed empty); prefs category/tags; country filter
- [x] 5.2 backend: Proof — returns real place ids or honest empty; foreign country excluded; no invented venues

## 6. Catalog HTTP (P3.6)

- [x] 6.1 backend: Add readiness + acquire DTOs and `src/api/catalog.py` routes: `GET /api/v1/sessions/{id}/catalog`, `POST /api/v1/catalog/acquire` (ownership checks; no generate)
- [x] 6.2 backend: Mount router in app; session projection MAY include catalog readiness without chat/HITL starting acquire
- [x] 6.3 backend: Proof — ASGI enqueue + readiness payload; foreign session denied
- [x] 6.4 frontend: Optional thin readiness/status + start-acquire control after trip_scope (no Build plan / generate CTA); or document API-only proof if FE deferred

## 7. Retrieve spans (P3.7)

- [x] 7.1 backend: Wrap retrieve with `ObsPort.span` (query/filters/empty signal); no-op when unconfigured
- [x] 7.2 backend: Proof — fake Obs records retrieve span; missing Obs keys → retrieve still succeeds

## 8. Proof tests, fail-soft, CI (P3.8)

- [x] 8.1 backend: Pytest cover acquire success/fail; country filter; empty retrieve; facade down → partial/empty; chat/HITL do not start acquire
- [x] 8.2 infra: Ensure CI pytest (or documented script) runs these checks; failures block merge
- [x] 8.3 docs: Align `system-docs/phase-slices/p3-catalog/` validation checkboxes with proofs; if blueprint and `llm.md` §7.3/§8 disagree, resolve both (no third shape)
