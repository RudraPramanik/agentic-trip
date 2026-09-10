# FE ↔ BE system map

High-level boundaries only. Details live in module docs.

> **Sibling product (not this map):** A separate conversational trip OS is documented in [`chat-first-trip-os.md`](./chat-first-trip-os.md). That bible is **not** Wandr generate/SSE traffic. Do not invent Wandr OpenAPI from it. The diagram below remains **Wandr** FE↔BE only.

```
┌──────────────────────────┐         cookies + JSON/SSE          ┌──────────────────────────┐
│  guideagent-frontend     │ ──────────────────────────────────▶ │  guideagent (FastAPI)    │
│  Next.js                 │◀──────────────────────────────────  │  /api/v1/...             │
│  localhost:3000          │         credentials: include        │  localhost:8000          │
└──────────────────────────┘                                     └──────────────────────────┘
         │                                                                    │
         │ NEXT_PUBLIC_API_URL only                                           │ PostGIS / Qdrant / Redis
         │ types from OpenAPI                                                 │ (docker compose, local)
         ▼                                                                    ▼
   types/generated/api.d.ts                                          src/* routers + services
```

## Auth / cookies

- FastAPI owns `wandr_session` and `wandr_token`. FE must use `credentials: "include"`; never store tokens in `localStorage`.
- Guest trip ownership: cookie session must match `Trip.session_id` or API returns 403 (distinct from “logged-in owner” 403).
- **Google OAuth chain (login = signup):** FE Login → navigate to `GET {API}/api/v1/auth/google` → Google consent → `GET {API}/api/v1/auth/callback` → API sets `wandr_token` → **redirect** to `{FRONTEND_URL}/auth/done` (success) or `{FRONTEND_URL}/auth/error?reason=…` (failure). FE `/auth/done` re-probes `GET /api/v1/auth/me`. No Auth0/NextAuth on FE.
- **Env:** BE `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`. FE `NEXT_PUBLIC_API_URL` only (no OAuth secrets).
- **Apply order / OpenSpec:** BE `oauth-frontend-url-bounce` first → FE `complete-google-login-ux`; parent vault `google-auth-login-signup`. Implementation = **two module PRs** (one per remote).
- Docs: `guideagent/docs/FE_guide.md`, `guideagent-frontend/AGENTS.md`, `guideagent-frontend/docs/app/system.md`

## OpenAPI / types

- Wire shapes: backend OpenAPI → FE `npm run gen:types` → `guideagent-frontend/types/generated/api.d.ts`
- HTTP only through `guideagent-frontend/lib/api/client.ts` (+ domain modules)
- Docs: `guideagent-frontend/docs/app/system.md`, `guideagent/docs/FE_guide.md`

## Destination intake / hub HITL

- **Search-first:** FE resolves a typed place name (not a map pin). City-scale → one `destination_id` → readiness/prepare → compose/generate.
- **Oversized (country/region):** BE additive `GET /api/v1/destinations/resolve?q=` returns `kind: hubs|ambiguous|destination`; FE HITL picks one hub, then existing prepare/generate. Do not plan on a country centroid alone.
- **Country scope:** Prepare and planner stop selection stay in `Destination.country` (radius scrape unchanged; no country polygon). Border-adjacent catalogs must not schedule foreign POIs.
- **Apply order / OpenSpec:** Parent `search-first-hub-planning` → **guideagent PR first** (resolve + country filter + OpenAPI) → **guideagent-frontend PR** (`gen:types` + hub HITL UX). Two module PRs.
- Docs: parent change `openspec/changes/search-first-hub-planning/`, `guideagent/docs/FE_guide.md`, `guideagent-frontend/docs/app/system.md`

## Planner SSE (`POST /api/v1/planner/generate`)

- FE: raw `fetch` + stream parse in `guideagent-frontend/lib/sse/planner.ts` (not `EventSource`); abort on unmount
- BE: `guideagent/src/planner/router.py` polls `request.is_disconnected()`; timeout → SSE `error` / `generation_timeout` (`guideagent/src/planner/service.py`, `PLANNER_GENERATION_TIMEOUT_SECONDS`)
- Pre-stream HTTP 409 `destination_not_ready` is not SSE
- Docs: `guideagent/docs/FE_guide.md`, `guideagent-frontend/docs/issues/issue.md` (timeout notes)

## Trips / GeoJSON

- After `itinerary_done`, navigate by `trip_id` then `GET /trips/{id}` + `GET /trips/{id}/geojson`
- GeoJSON is raw FeatureCollection (not `ApiResponse`); built by `TripService.build_geojson` (decode-only, no network I/O)
- Road LineStrings need BE polylines: set `ROUTING_BACKEND=hybrid` (haversine times + OSRM fail-soft geometry). Default `haversine` → Point-only overlay
- FE: `lib/api/trips.ts`, `features/trips/use-trip-geojson.ts`, `features/trips/trip-map.tsx`; paint LineStrings when present; never invent coordinates; list-first if map tiles fail
- **Apply order / OpenSpec:** BE `hybrid-routing-trip-polylines` first → FE `trip-route-polyline-map` (docs/verify); parent vault change `cross-trip-route-polylines`. Implementation = **two module PRs** (one per remote), not parent app code
- Docs: `guideagent/docs/FE_guide.md` § GeoJSON, `guideagent-frontend/docs/app/system.md`

## Map basemap / place media / guidebook UI

- **Basemap:** MapLibre + `NEXT_PUBLIC_MAP_STYLE_URL` (MapTiler street). Optional `NEXT_PUBLIC_MAP_SATELLITE_STYLE_URL` for satellite/hybrid toggle — **FE-only**, no API.
- **Place photos:** Resolved **after** generate (not on SSE hot path). BE `MEDIA_SOURCES` facade (`wikimedia`, `osm`, `opentripmap`; future `google`) → `GET /places/{id}/media` with normalized `PlaceMedia` DTO. FE uses shared image component + category gradient fallback.
- **Guidebook UI:** Layla-shaped trip detail (hero, photo stop cards, stay block from `preferences.accommodation_label`). PDF export deferred.
- **Apply order / OpenSpec:** Parent `free-media-map-guidebook` (vault) → optional FE `map-basemap-toggle` (P1, can ship alone) → BE `place-media-enrich` → FE `guidebook-trip-ui`. Implementation = **module PRs** (guideagent + guideagent-frontend), not parent app code.
- **Planning doc:** [`free-media-map-guidebook.md`](./free-media-map-guidebook.md)

## Local run (unchanged)

- BE: `guideagent/docker-compose.yml` → API `:8000`
- FE: `guideagent-frontend` → `npm run dev` → `:3000`
