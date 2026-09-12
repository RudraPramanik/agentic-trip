## 1. Local env for NVIDIA + Gemini

- [x] 1.1 infra: Copy required local settings from `.env.demo` into `.env` (not committed): `DATABASE_URL`, CORS/frontend URLs as needed, `LLM_MODEL` / `LLM_API_KEY` / `LLM_API_BASE` for NVIDIA NIM primary, `LLM_MODEL_FALLBACKS` including Gemini, `GEMINI_API_KEY`, `EMBEDDING_MODEL`; never commit secrets or paste keys into docs
- [x] 1.2 infra: Proof — API boots with `.env`; Settings reads LLM trio; document which vars were needed (names only)

## 2. GuidebookExport DTO (P5.1)

- [x] 2.1 backend: Add `GuidebookExport` types + pure `to_guidebook_export(trip)` in `src/modules/trips/export.py` (cover, hubs, days, stops, narratives, map points; no LLM)
- [x] 2.2 backend: Wire `TripService.export_guidebook`; Proof — unit schema: fields cover UI + future PDF; mapping does not invent place ids/coords

## 3. Trip id on draft + get (P5.2 prep)

- [x] 3.1 backend: On successful `persist_draft`, assign durable `trip_id` (UUID), set session `trip_id`, persist minimal owned trip artifact (table or equivalent) with draft itinerary; Explore last-trip stays locked
- [x] 3.2 backend: Implement `TripService.get_trip` with guest ownership; backfill `trip_id` for older drafts if needed
- [x] 3.3 backend: Proof — unit: success persist yields trip_id; foreign owner denied; validation fail still no success persist

## 4. Trip get + export routes (P5.2)

- [x] 4.1 backend: Add `src/api/trips.py` with `GET /api/v1/trips/{id}` and `GET /api/v1/trips/{id}/export`; mount router; ownership via guest cookie
- [x] 4.2 backend: Proof — ASGI: owner get/export match DTO schema; foreign session denied; no Wandr paths

## 5. Media facade stub (P5.6)

- [x] 5.1 backend: Add `src/modules/media/` `MediaProvider` stub `get_place_media` → empty/fail-soft; do not wire into generate_graph
- [x] 5.2 backend: Proof — unit: stub empty; generate path does not call media (spy/fake)

## 6. FE guidebook (P5.3)

- [x] 6.1 frontend: Add guidebook views (`GuidebookView` / cover / leg sections) fetching trip get and/or export; navigate from generate `done` using `trip_id`
- [x] 6.2 frontend: Proof — component or manual: reopen trip shows days/stops from draft

## 7. MapLibre points map (P5.4)

- [x] 7.1 frontend: Add MapLibre `TripMap` plotting stop points; polyline layer only if route geometry present; no crow-flies-as-roads; list-first if style fails; env style URL with OSM fallback
- [x] 7.2 frontend: Proof — test or note: missing geom → points only; v1 no polyline producer

## 8. Empty booking block (P5.5)

- [x] 8.1 frontend: Render hollow `BookingPlaceholder` (stays/flights/activities) with no prices/vendor SDKs
- [x] 8.2 frontend: Proof — UI shows coming-later / empty without rates

## 9. Session projection trip_id

- [x] 9.1 backend: Ensure session GET and/or generate `done` payload includes `trip_id` after successful draft
- [x] 9.2 backend: Proof — ASGI or unit: draft session projection exposes trip_id for guidebook navigation

## 10. Local terminal + browser validation + CI

- [x] 10.1 infra: Ensure CI pytest (or documented script) runs GuidebookExport schema, trip ASGI ownership, media-not-on-generate checks; failures block merge
- [x] 10.2 backend: Local terminal smoke — Compose API/db up; after generate (or fixture draft), curl/httpx `GET /api/v1/trips/{id}` and `.../export`; assert days/map points; foreign cookie denied
- [x] 10.3 frontend: Local browser smoke — guest → Build plan → open guidebook → days + map points + empty booking; no fake polyline; map style fail still shows list
- [x] 10.4 docs: Align `system-docs/phase-slices/p5-guidebook-map/` validation checkboxes with proofs; if blueprint and `llm.md` §5–6 disagree, resolve both (no third shape)
