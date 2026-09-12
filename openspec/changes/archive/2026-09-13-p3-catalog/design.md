## Context

See `proposal.md` for why. P2 left confirmed `trip_scope` on sessions, nullable session `catalog` JSONB, an empty `modules/catalog` package, and a stub `PlaceRepository` port (`retrieve` only). Compose runs PostGIS + API only — no Redis/worker yet. `ObsPort` already supports fail-soft spans.

Implementation follows `system-docs/phase-slices/p3-catalog/` (P3.1–P3.8, guardrails, validation), `system-docs/llm.md` §7.3 / §8, `SHARED-SWE-LLD.md`, and `SHARED-FAIL-SOFT.md`. Call chain stays locked: routers → `CatalogService` → ports/repos/adapters; workers call `CatalogService` (no Overpass HTTP inside worker modules beyond composition-root wiring).

## Goals / Non-Goals

**Goals:**

- Place model + PostGIS GiST repo (`upsert_many`, `retrieve`).
- Places facade (Overpass + OTM adapters) mapping to `Place`.
- `CatalogService.acquire` / `readiness` / `retrieve` with typed results.
- ARQ `acquire_catalog` + Compose Redis/worker; bounded retry → failed.
- Catalog HTTP readiness + enqueue; session ownership checks.
- Retrieve obs spans (or no-op); country filter on upsert and retrieve.
- Proof tests + CI bar for validation.md checks.

**Non-Goals:**

- Generate, Build plan CTA, packing, itinerary persist (P4).
- Qdrant / vector retrieve; map/guidebook; Explore; booking.
- Wandr paths/DTOs/env; country-centroid scrape; invented POIs/coords/polylines.
- Auto-acquire on scope confirm or every chat turn.

## Decisions

### D1 — Place persistence is PostGIS-first with GiST (P3.1)

Alembic migration adds a `places` table (or equivalent): stable id, name, geometry (`geometry(Point,4326)` or MultiPoint as needed), category/tags (JSONB or array), `country_code`, provider source ids, updated_at. GiST index on geometry. `PlaceRepository` gains `upsert_many(places)` and implements `retrieve(scope, prefs)` via bbox ∩ filters + country. Session `catalog` JSONB stores readiness projection (`status`, `place_count`, `job_id?`, error note) — not the full POI dump.

**Why not** store only in Redis: need spatial query + durable ids for later validate.  
**Why not** Qdrant in P3: blueprint non-goal; PostGIS is v1 retrieve.  
**Alternative:** GeoJSON blobs without GiST. Rejected — unbounded scans violate SWE locks.

### D2 — PlacesFacade with Overpass + OTM adapters (P3.2)

`PlacesFacade.fetch_for_scope(scope) -> list[Place] | PartialPlaces` composes `OverpassAdapter` and `OtmAdapter` behind httpx timeouts. Mapping is adapter-local; facade merges/dedupes by provider id or name+approx coord within tolerance. Down/timeout → empty list contribution; overall typed partial when any provider fails but another succeeds.

**Why facade:** SHARED-SWE-LLD — multiple free providers, one port.  
**Why not** call Overpass from `CatalogService` directly: keeps vendor HTTP in adapters.  
**CI:** mock httpx; no live Overpass required for green.

### D3 — CatalogService owns acquire/readiness/retrieve use-cases (P3.3, P3.5)

- `acquire(session_id)`: load session + `trip_scope`; refuse country-without-hubs (honest failed/needs hubs); call facade for region/hub polygons; country-filter; `upsert_many`; write readiness `ready|partial|failed`.
- `readiness(session_id)`: return session catalog projection.
- `retrieve(scope, prefs)`: repo retrieve + typed `RetrieveResult` (ids or empty).

Enqueue path used by HTTP may set status `pending`/`running` then hand off to ARQ; worker re-enters `CatalogService.acquire` (idempotent status transitions).

**Why not** put acquire logic only in the worker: service is the testable use-case; worker is a runner.  
**Country-without-hubs:** align with P2 country-long hubs/HITL — do not silent-centroid.

### D4 — ARQ + Redis worker for acquire_catalog (P3.4)

Compose adds `redis` and `worker` services. Worker entry imports ARQ settings and registers `acquire_catalog(ctx, session_id)`. Bounded retries (settings constant, e.g. 3) then mark session catalog `failed`. API composition root enqueues via ARQ; if Redis down at enqueue time → honest error / failed readiness, health still OK.

**Why ARQ:** architecture L12 + LLD §7.3.  
**Why not** in-process acquire on the request thread: acquire is long-running; keep request thin.  
**Idempotency:** if status already `ready` and place_count > 0, re-enqueue may no-op or refresh with explicit status; never double-write success without clear transition.

### D5 — Catalog HTTP (P3.6)

- `GET /api/v1/sessions/{id}/catalog` → readiness DTO (`ready` bool and/or `status`, `place_count?`).
- `POST /api/v1/catalog/acquire` body `{ "session_id" }` → `{ "job_id", "status" }`.
- Router: parse/serialize + Depends; ownership via AuthPort/session repo; no vendor HTTP.
- Optional thin FE: show readiness after scope confirm and a control to start acquire — **not** Build plan. Prefer documenting API proof if FE is deferred; if FE is included, keep it status-only.

### D6 — Retrieve spans (P3.7)

Wrap `CatalogService.retrieve` with `ObsPort.span("catalog.retrieve", ...)` including filter keys and `empty` bool. No-op Obs remains default without keys.

### D7 — Testing and CI bar (P3.8 / SWE)

| Layer | Proof |
|-------|--------|
| Unit | Place upsert + bbox; facade mock down→empty/partial; acquire uses region/hubs; country filter; empty retrieve |
| Worker | ARQ success + failure status (fake redis/queue or in-process job runner test double) |
| ASGI | catalog GET + POST acquire enqueue; foreign session denied |
| Obs | retrieve span recorded with fake Obs, or no-op path |
| Negative | no country-centroid; chat/HITL does not start acquire; no invented POIs |
| CI | pytest job runs suite; failures block |

### D8 — Error / fallback map (slice)

| Kind | Fallback |
|------|----------|
| Overpass/OTM down | empty/partial; honest readiness |
| Thin catalog | no foreign/centroid fill |
| ARQ/Redis down | marked failed / honest enqueue error |
| Empty retrieve | typed empty (HITL at generate later) |
| Obs down | no-op |
| Country-without-hubs | refuse / failed / require hubs — no silent scrape |

### D9 — Scalability / reliability posture (v1)

- Spatial GiST keeps retrieve O(log n + k) not full scan.
- Acquire scoped to hubs/region polygons bounds work; country-wide scrape forbidden.
- Worker horizontal scale later via more ARQ workers sharing Redis; service remains stateless aside from DB.
- Deduped upserts and status machine keep retries safe.
- Provider timeouts + circuit-style empty results protect the API from vendor hang.

## Risks / Trade-offs

- **[Risk] Overpass rate limits / flaky live calls** → Mitigation: mock in CI; timeouts; optional cache later; polite User-Agent.
- **[Risk] Large hub polygons → heavy acquire** → Mitigation: bbox/hub limits in settings; partial readiness; never unbounded country scrape.
- **[Risk] Redis operational burden vs P0 “API boots without Redis”** → Mitigation: keep health independent; only acquire path requires queue.
- **[Trade-off] Dual providers may disagree on POIs** → Mitigation: dedupe heuristic; prefer stable provider ids; document partial when one side fails.
- **[Risk] FE scope creep into generate CTA** → Mitigation: blueprint non-goal; tasks exclude Build plan.
- **[Trade-off] Optional FE vs API-only proof** → Mitigation: ASGI proofs are mandatory; FE status control is optional and thin if present.

## Migration Plan

1. Land places migration + repository; wire PlaceRepository in composition root.
2. Land adapters + facade; unit mocks.
3. Land CatalogService acquire/readiness/retrieve + session catalog projection writes.
4. Add Redis/worker Compose + ARQ job; enqueue from service/API.
5. Mount catalog router; expand CI pytest.
6. Optional thin FE readiness; validation checklist.
7. Rollback: revert deploy; places table can remain unused; disable worker/enqueue via config.

## Open Questions

- None material for specs/tasks: FE acquire control is optional (API proofs suffice); provider priority Overpass-first then OTM merge is the default assumption recorded in D2.
