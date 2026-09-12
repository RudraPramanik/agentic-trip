## Why

P4 shipped abortable generate into a reopenable **draft** itinerary, but guests still cannot open a guidebook view, map those stops, or fetch a stable export JSON for UI (and later PDF). Without P5 the “map-backed trip artifact” product law stays unproven and P5b has no DTO. P4 is archived complete; P5 is the next product proof.

Work type: **cross-cutting** (backend trips export + trip read APIs + media stub; frontend guidebook + MapLibre + empty booking block; tests + local browser/terminal validation). Not docs-only.

## What Changes

- Implement `GuidebookExport` as the single JSON view-model (cover, hubs, days, stops, narratives, map points) via pure `to_guidebook_export(trip)` / `TripService.export_guidebook` — mapping from structured trip only; no LLM rewrite of days/stops.
- Expose product routes `GET /api/v1/trips/{id}` and `GET /api/v1/trips/{id}/export` with guest ownership checks (no Wandr paths).
- Ensure draft reopen has a stable trip id (assign/persist on draft if missing) so FE can load guidebook after generate.
- Ship FE guidebook (cover, hub sequence, per-leg narrative + POIs) consuming export/trip JSON.
- Ship MapLibre trip map: **points always**; polyline layer only if routing geometry already exists on the trip (v1 is points-only; never invent crow-flies as roads).
- Render hollow booking placeholder in guidebook UI (no rates, no vendor SDKs; P8 owns booking API).
- Add off–hot-path `MediaProvider` stub (`get_place_media` → empty/fail-soft); generate MUST NOT call media.
- Local validation: terminal ASGI smoke for trip get/export; browser smoke for guidebook + map + empty booking; configure local `.env` from `.env.demo` for **NVIDIA NIM primary + Gemini fallback/embeddings** (keys stay out of git/docs).
- Follow `system-docs/phase-slices/p5-guidebook-map/` (P5.1–P5.6, guardrails, validation), `system-docs/llm.md` §5–6, `SHARED-SWE-LLD.md`, and `SHARED-FAIL-SOFT.md`.

**Non-goals:** PDF bytes / print pipeline (P5b); enrich worker / real media providers; fake polylines or invented coords/POIs; revise (P6); Explore (P7); booking vendor API (P8); OAuth saved-trip save API; Wandr paths/DTOs/env; second narrative pipeline for PDF.

**BREAKING:** none for existing dialogue/catalog/generate clients beyond additive trip routes. **Spec-level:** `api-foundation` flips trip get + export from non-product to product for this slice; explore/booking APIs remain forbidden until their slices; PDF remains P5b.

## Capabilities

### New Capabilities

- `trip-guidebook-map`: Stable `GuidebookExport` mapping + trip get/export HTTP; FE guidebook + MapLibre points map; empty booking UI slot; media port stub off generate hot path; local terminal/browser proofs.

### Modified Capabilities

- `api-foundation`: Allow `GET /api/v1/trips/{id}` and `GET /api/v1/trips/{id}/export` as product routes once this slice ships; keep explore/booking/PDF non-product until their slices.
- `fail-soft-boundaries`: Tighten P5 map/media fallbacks — missing routing geometry → points only; map style fail → list-first guidebook; missing media → category/gradient honest fallback (never fake venue photo claim); media never on generate path.
- `booking-placeholder`: Clarify that P5 ships the hollow stays/flights/activities UI adjacent to guidebook for reopenable draft trips (no prices); booking HTTP remains P8.
- `guest-chat-sessions`: After successful generate, session projection MAY expose `trip_id` for guidebook navigation; chat/HITL/scope confirm still MUST NOT start generate.
- `conversational-trip-planner`: Clarify reopenable draft trip is viewable as guidebook + mapped stops via trip routes / FE; v1 map is points-only unless geometry exists.

## Impact

- **Code / APIs:** `src/modules/trips/` (`export.py`, `TripService.get_trip` / `export_guidebook`, optional trips row / `trip_id` on draft); `src/api/trips.py`; `src/modules/media/` stub port; composition-root wiring; ownership via guest cookie + session/trip link.
- **Frontend:** guidebook views + MapLibre map + booking placeholder empty state; navigation from post-generate draft to trip guidebook; list-first fallback if map style fails.
- **Tests / CI:** unit schema for `GuidebookExport`; ASGI get/export ownership; map payload never invents polyline; media stub unused by generate; FE smoke notes; local terminal + browser validation in tasks.
- **Env / local run:** Apply copies non-secret config + LLM settings from `.env.demo` into `.env` for NVIDIA (`LLM_*` / NIM) + Gemini (`GEMINI_API_KEY`, embedding model) — never commit secrets.
- **Reliability / scale (v1 posture):** Export is pure mapping (CPU-cheap, cacheable later); trip read is ownership-scoped; media off hot path keeps generate latency bounded; MapLibre client-side points scale with stop count; DTO shared with future PDF avoids dual pipelines; routers → services → ports only.
- **Docs:** implement against existing `system-docs/phase-slices/p5-guidebook-map/`; if blueprint and `llm.md` disagree, resolve both in this change (no third shape).
