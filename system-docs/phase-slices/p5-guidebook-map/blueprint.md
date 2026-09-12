# P5 Guidebook UI + map + export DTO — blueprint

> Status: implemented via OpenSpec `p5-guidebook-map` (GuidebookExport, trip get/export, FE guidebook + MapLibre points, hollow booking, media stub).
> LLD: [`../../llm.md`](../../llm.md) §5, §6

## Goal

Frontend trip guidebook + MapLibre map; backend GuidebookExport DTO; booking placeholder empty block in UI.

## Scope / modules

frontend features/trip|map; modules/trips export; media optional later

## Step plan

Implement **one sub-phase at a time**.

### P5.1 — GuidebookExport DTO

- **Goal:** Stable JSON view-model = future PDF input.
- **Modules:** `src/modules/trips/export.py`
- **Types:** `GuidebookExport` (cover, hubs, days, stops, narratives, map points)
- **Functions:** `to_guidebook_export(trip) -> GuidebookExport`
- **Services:** `TripService.export_guidebook`
- **Routes / APIs:** none yet
- **Algorithms / data:** map from structured trip only; no LLM rewrite of structure
- **Depends on:** P4.7
- **Proof:** schema test: fields cover UI + PDF needs
- **Non-goals:** PDF bytes

### P5.2 — Trip get + export routes

- **Goal:** Read trip and export JSON.
- **Modules:** `src/api/trips.py`
- **Types:** trip response DTO
- **Functions:** `get_trip`, `export_trip`
- **Services:** `TripService`
- **Routes / APIs:** `GET /api/v1/trips/{id}`, `GET /api/v1/trips/{id}/export`
- **Algorithms / data:** —
- **Depends on:** P5.1
- **Proof:** ASGI export matches DTO schema
- **Non-goals:** Wandr trip paths

### P5.3 — FE guidebook

- **Goal:** Cover, hub sequence, per-leg narrative + POIs.
- **Modules:** `frontend/` guidebook views
- **Types:** `GuidebookView`, `Cover`, `LegSection`
- **Functions:** fetch export/trip and render
- **Services:** none
- **Routes / APIs:** consumes P5.2
- **Algorithms / data:** —
- **Depends on:** P5.2
- **Proof:** reopen trip shows days in UI (manual or component test)
- **Non-goals:** PDF

### P5.4 — MapLibre

- **Goal:** Stops as points; polyline only if routing geometry exists.
- **Modules:** `frontend/` map
- **Types:** `TripMap`
- **Functions:** plot stops; optional line layer if geom present
- **Services:** none
- **Routes / APIs:** uses trip map payload
- **Algorithms / data:** no client-invented crow-flies as “roads”. **v1 is points-only** unless a later slice stores route geometry on the trip.
- **Depends on:** P5.3
- **Proof:** test or note: missing geom → points only; v1 has no polyline producer
- **Non-goals:** fake polylines; inventing route geometry in this slice

### P5.5 — Empty booking block in UI

- **Goal:** Hollow stays/flights/activities slot with no rates.
- **Modules:** `frontend/` guidebook
- **Types:** `BookingPlaceholder`
- **Functions:** render empty state
- **Services:** none (P8 owns API)
- **Routes / APIs:** none required (static empty OK)
- **Algorithms / data:** —
- **Depends on:** P5.3
- **Proof:** UI shows coming-later without prices
- **Non-goals:** vendor SDKs

### P5.6 — Media facade stub

- **Goal:** Optional media port stub; not on generate hot path.
- **Modules:** `src/modules/media/`
- **Types:** `MediaProvider` port stub
- **Functions:** `get_place_media(place_id)` → empty/fail-soft
- **Services:** none on generate
- **Routes / APIs:** none required
- **Algorithms / data:** —
- **Depends on:** P0.5
- **Proof:** generate path does not call media; stub returns empty
- **Non-goals:** enrich worker

## Proof

Reopen trip shows days + mapped stops; export DTO matches UI fields for future PDF

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
