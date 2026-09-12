## Context

See proposal.md — Why. P4 archived: generate persists `status=draft` itinerary on the guest session via `TripService.persist_draft`; session may hold optional `trip_id` but get/export routes and GuidebookExport do not exist yet. Frontend is a chat shell with Build plan CTA and no trip guidebook/map. Phase docs: `system-docs/phase-slices/p5-guidebook-map/`; contracts in `system-docs/llm.md` §5–6. Constraints: routers → services → ports; no Wandr paths/DTOs; no invented coords/POIs/polylines; GuidebookExport is the single view-model for UI + future PDF; media off generate hot path.

## Goals / Non-Goals

**Goals:**

- Stable `GuidebookExport` + `TripService.get_trip` / `export_guidebook` with ownership.
- Product `GET /api/v1/trips/{id}` and `.../export`.
- Assign durable `trip_id` on successful draft so FE can reopen.
- FE guidebook + MapLibre points map + hollow booking block.
- Media port stub that generate never calls.
- Local `.env` for NVIDIA primary + Gemini fallback/embeddings; terminal + browser validation.

**Non-Goals:**

- PDF bytes (P5b); real media providers/enrich worker; polyline producer; booking HTTP (P8); OAuth save; Explore unlock from draft; Wandr APIs.

## Decisions

### 1. Trip identity: assign UUID on draft persist; store on session + optional trips row

**Choice:** On successful `persist_draft`, if `trip_id` is missing, allocate a UUID, set `session.trip_id`, and persist a minimal trips artifact row (or equivalent JSON keyed by that id) owned by the guest/session so `GET /trips/{id}` resolves independently of “load session then dig itinerary.”

**Why:** Blueprint and `llm.md` require `/trips/{id}`; session-only nested itinerary without an id blocks guidebook deep-links and export.

**Alternatives:** Use `session_id` as trip id (couples chat session to trip URL forever); defer trips table until OAuth save (breaks P5 routes).

### 2. GuidebookExport is a pure mapper, not a graph node

**Choice:** `to_guidebook_export(trip) -> GuidebookExport` in `src/modules/trips/export.py`; `TripService.export_guidebook` loads owned trip then maps. No LLM, no catalog re-fetch required for structure.

**Why:** Guardrail — UI and PDF share one DTO; structure already validated at generate.

**Alternatives:** Re-run narrative at export (dual pipeline, drift); FE invents view-model from raw session (PDF later forks).

### 3. Map payload: points array always; `route_geometry` optional omit in v1

**Choice:** Export/map DTO includes stop points (`place_id`, lat/lng, day index). Omit polyline / only include if trip already has geometry. FE MapLibre: circle/symbol layer for points; line layer gated on present geom. No client haversine-as-road.

**Why:** P5.4 + fail-soft; v1 has no polyline producer.

**Alternatives:** Always draw crow-flies (forbidden); wait for OSRM geom slice before any map (delays product proof).

### 4. FE composition: trip route after generate; list-first if map fails

**Choice:** After generate `done` with `trip_id`, navigate or panel-open guidebook that fetches export (or get+export). MapLibre via env style URL (`NEXT_PUBLIC_MAP_STYLE_URL` or OSM fallback). Style error → hide map / show list only.

**Why:** Matches guardrails; keeps chat shell usable without basemap keys.

**Alternatives:** Embed map only in PDF later; require MapTiler key with no fallback.

### 5. Booking UI hollow locally; no booking API in P5

**Choice:** Static `BookingPlaceholder` component in guidebook. No `GET .../booking` until P8.

**Why:** Blueprint P5.5 vs P8 API ownership.

### 6. Media stub module, never wired into generate_graph

**Choice:** `src/modules/media/` with `MediaProvider.get_place_media(place_id) -> []` fail-soft. Composition may register stub; generate deps MUST NOT include it. Proof: unit/integration assert generate path does not call media.

**Why:** P5.6; generate latency/reliability.

### 7. Local LLM env: NVIDIA primary, Gemini fallback/embeddings

**Choice:** At apply/validation, copy from `.env.demo` into local `.env` (not committed): `LLM_MODEL` / `LLM_API_*` for NVIDIA NIM, `LLM_MODEL_FALLBACKS` including Gemini, `GEMINI_API_KEY`, `EMBEDDING_MODEL`. Prefer existing Settings/`LLM_*` trio; do not invent Wandr env names. Never paste secrets into OpenSpec artifacts or git.

**Why:** User-requested local stack for full workingness through generate → guidebook.

### 8. Reliability / scale posture

**Choice:** Pure export (O(stops), cacheable later); ownership check before read; points-only map scales with stop count; media off hot path; DTO frozen for P5b; keep routers thin.

**Alternatives:** Compute export at generate and store denormalized copy only (premature; mapper is cheap).

## Risks / Trade-offs

- [Drafts without trip_id from pre-P5 generates] → Mitigation: backfill id on first get/export or next persist; document one-time migration in tasks.
- [MapTiler/OSM style flaky offline] → Mitigation: list-first fallback + documented env.
- [FE MapLibre bundle size] → Mitigation: dynamic import map component; keep chat route light.
- [Secrets in `.env.demo`] → Mitigation: copy to `.env` locally only; never commit `.env`; rotate if leaked.
- [Scope creep into PDF/media enrich] → Mitigation: non-goals + P5b/P8 ownership in tasks.

## Migration Plan

1. Implement backend export + trip id on draft + routes behind existing guest auth.
2. Add FE guidebook/map/booking placeholder; wire post-generate navigation.
3. Add media stub; verify generate untouched.
4. Configure local `.env` from `.env.demo` (NVIDIA + Gemini).
5. Run unit/ASGI + terminal curl smoke + browser smoke per validation.md.
6. Rollback: leave routes unused / feature-flag FE panel; draft itinerary on session remains valid.

## Open Questions

None material for this slice. Minor: exact MapLibre style provider URL left to env at apply time (OSM fallback acceptable).
