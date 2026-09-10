# Symptom → FE / BE paths

Verify paths before editing. Prefer module docs over guessing.

| Symptom | Check FE | Check BE | Notes / docs |
|---------|----------|----------|--------------|
| Login lands on API JSON page (not app) | `app/auth/done/page.tsx`, `features/auth/start-login.ts`, `NEXT_PUBLIC_API_URL` | `src/auth/router.py` (`FRONTEND_URL` redirect after callback), `src/config.py` | OAuth callback must redirect to `{FRONTEND_URL}/auth/done` with `wandr_token` Set-Cookie. OpenSpec: BE `oauth-frontend-url-bounce`, FE `complete-google-login-ux`. Apply BE first. `guideagent/docs/FE_guide.md` §11 |
| OAuth error 404 on API host | `app/auth/error/page.tsx` | `src/auth/router.py` (failure redirect must use `{FRONTEND_URL}/auth/error`) | Errors must not redirect to `/auth/error` on API host only. Same module changes as above |
| Guest 403 / cookie split (`localhost` vs `127.0.0.1`) | `NEXT_PUBLIC_API_URL` must match browser origin family; use one host consistently | `CORS_ALLOWED_ORIGINS` must list the FE origin you actually use | Different registrable hosts = different cookie jars under `SameSite=Lax`. Do not mix `localhost:3000` app with `127.0.0.1:8000` API URL in env |
| `AUTH0_*` in frontend `.env` | Remove Auth0 vars — FastAPI owns auth | N/A (OAuth secrets live in `guideagent/.env` only) | Next.js must not use Auth0/NextAuth/Better Auth for MVP. Only `NEXT_PUBLIC_*` in FE env |
| Generate hangs, stalls, or ends with timeout | `lib/sse/planner.ts`, `features/planner/compose-form.tsx` (AbortSignal, terminal SSE `error` UI — do **not** “fix” by only lengthening client abort) | `src/planner/router.py` (`is_disconnected`), `src/planner/service.py` (`generation_timeout`), `src/config.py` (`PLANNER_GENERATION_TIMEOUT_SECONDS`) | Often API graph budget, not FE. See `guideagent-frontend/docs/issues/issue.md`, `guideagent/docs/FE_guide.md` |
| HTTP 409 before any SSE (`destination_not_ready`) | Readiness gate UI / compose flow; do not treat as stream error | Destination readiness / place floor; `DestinationNotReadyError` | Pre-stream failure — `guideagent/docs/FE_guide.md` |
| Country/region search plans a useless centroid or skips city pick | Home resolve/hub HITL UI; must not call prepare on country shell alone | `GET /destinations/resolve` oversized → `kind: hubs`; Nominatim scale signals | Parent `search-first-hub-planning`. Apply BE OpenAPI first, then FE. Search-only clients still work |
| Trip/stops leak across a border (e.g. Darjeeling → Nepal) | Do not use map/`base_lat` to “fix” country; report foreign stops | Prepare country filter + planner same-country select; `Destination.country` | Radius prepare stays; no polygon scrape. Re-prepare may be needed to clean old catalogs |
| Guest 403 on trip vs owner 403 | Cookie `credentials: "include"`; distinct copy for guest-mismatch; claim flow | `wandr_session` vs `Trip.session_id`; ownership checks on trips router/service | Do not spoof session UUID. `localhost` vs `127.0.0.1` splits cookies. FE `AGENTS.md` + `docs/issues/issue.md` |
| Map empty / no route line | `use-trip-geojson.ts`, `features/trips/trip-map.tsx`; list-first if tiles fail; Point-only if no LineStrings — **never invent crow-flies** | `GET /trips/{id}/geojson`, `TripService.build_geojson`; geometry via `ROUTING_BACKEND` (`haversine` = Point-only; `hybrid` = haversine times + OSRM polylines) | Raw GeoJSON, not `ApiResponse`. OpenSpec: BE `guideagent/openspec/changes/hybrid-routing-trip-polylines`, FE `guideagent-frontend/openspec/changes/trip-route-polyline-map`. Apply BE first, then FE docs/verify; two module PRs. Old trips stay Point-only until regenerate/reoptimize. `guideagent/docs/FE_guide.md` §15 |
| Types / DTO drift | `types/generated/api.d.ts`, `npm run gen:types`, `scripts/generate-api-types.mjs` | OpenAPI schema / Pydantic models served by API | Regenerate; do not hand-patch generated types |
| FE “missing LLM keys” suspicion on generate | Confirm only `NEXT_PUBLIC_*` is used | API `.env` LLM / embeddings / MapTiler secrets | Next does not send backend secrets. `docs/issues/issue.md` |

## How to extend

Add a row only when a real cross-bug is documented. Link concrete paths or existing docs — never speculative endpoints.
