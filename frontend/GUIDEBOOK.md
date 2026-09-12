# P5 Guidebook UI — local smoke notes

## Component / behavior proofs

- **Guidebook days (6.2):** After generate `done` with `trip_id`, Open guidebook loads `GET /api/v1/trips/{id}/export` and renders cover + day sections + stops from draft.
- **Map points only (7.2):** `TripMap` plots `map_points`. Polyline layer is gated on `route_geometry`; v1 export omits it — **no crow-flies-as-roads**. Style fail → list-first message; day list remains.
- **Empty booking (8.2):** `BookingPlaceholder` shows “Coming later” with empty stays/flights/activities and **no prices**.

## Browser smoke

1. Start API + FE (`uv run` / Compose + `npm run dev`).
2. Guest chat → confirm scope → (optional acquire) → **Build plan**.
3. On draft ready, open guidebook: days + map points + empty booking.
4. Confirm no polyline when geometry missing; break map style URL → list still usable.
