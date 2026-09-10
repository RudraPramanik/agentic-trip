# Free-tier map, place media & guidebook UI — planning doc

> **Status:** planning only — no module code shipped yet. Implementation deferred to future `map-basemap-toggle`, `place-media-enrich`, and `guidebook-trip-ui` module changes.  
> **Purpose:** discussion doc for FE + BE changes. Free providers v1; Google-ready facade so a future paid tier is **config + adapter**, not a rewrite.

---

## 1. Executive summary

| Area | v1 (free) | Future (paid gate) | Code churn if we design right |
|------|-----------|-------------------|-------------------------------|
| **Map look / satellite** | MapTiler `streets-v2` + `satellite`/`hybrid`/`outdoor` toggle | Optional Google map tiles (unlikely needed) | **Low** — env URL swap + optional provider interface |
| **Place photos** | Wikimedia + OSM `image` tag + OpenTripMap preview | Google Places Photos | **Low** — new provider class + env key |
| **Rich POI data** | OSM/Overpass + OpenTripMap (already facaded) | Google Places / Geoapify | **Low** — same `fetch_destination_pois` pattern |
| **Hotels** | Text `accommodation_label` + optional OSM `tourism=hotel` | Google Places lodging | **Medium** — new lodging domain, not media swap |
| **Layla UI** | Hero + photo stop cards + stay block | Same + PDF export | **Low** for UI; PDF is new surface |
| **When images load** | After generate (enrich job or on-demand API) | Same | **None** — already off hot path |

**Answer to “will Google need lots of code changes?”**  
**No**, if we mirror the existing **places facade** (`PLACES_SOURCES`) with a **media facade** (`MEDIA_SOURCES`) and a stable `PlaceMedia` DTO on the wire. Google becomes: enable provider, set API key, possibly enable billing. UI and trip models stay the same.

---

## 2. Current state (as-built)

### Frontend (`guideagent-frontend`)

| Piece | Today |
|-------|--------|
| Map | MapLibre in `features/trips/trip-map.tsx` |
| Style | `NEXT_PUBLIC_MAP_STYLE_URL` → MapTiler `streets-v2` (or dev OSM fallback) |
| Trip UI | Text stop cards, day timeline, markdown narrative |
| Images | `components/category-art.tsx` gradients; honest “not a photo of this venue” |
| Explore | `features/explore/feed-card.tsx` — same gradient pattern |

### Backend (`guideagent`)

| Piece | Today |
|-------|--------|
| Places | `Place` model: name, category, lat/lng, `summary`, `enriched_tags` — **no media** |
| POI ingest | `fetch_destination_pois` facade: Overpass (+ optional OpenTripMap) |
| Enrich | LLM text only (`places/service.py` `enrich_place`) |
| Generate | 45s SSE budget — must not add image HTTP |

---

## 3. Architecture (target)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AFTER TRIP SAVED                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  guideagent                                                              │
│    MEDIA_SOURCES=wikimedia,osm,opentripmap   (future: ,google)          │
│    src/geo/media/                                                        │
│      MediaProvider protocol                                              │
│      ├── WikimediaProvider                                               │
│      ├── OsmImageTagProvider                                             │
│      ├── OpenTripMapPreviewProvider                                      │
│      └── GooglePlacesPhotoProvider  (stub / future)                      │
│    resolve_place_media(place) → list[PlaceMedia]                         │
│    Trigger: enrich script | GET /places/{id}/media | batch on trip view  │
│                                                                          │
│  guideagent-frontend                                                     │
│    PlaceMediaCard — url + attribution + gradient fallback                │
│    TripMap — street | satellite toggle, re-layer GeoJSON                 │
│    GuidebookTripDetail — hero, day cards, stay block                     │
└─────────────────────────────────────────────────────────────────────────┘

GENERATE HOT PATH (unchanged)
  search → rank → schedule → write_narrative → persist
  (no media HTTP)
```

### Stable wire shape (proposed — module OpenSpec must formalize in OpenAPI)

```typescript
// Conceptual — becomes components["schemas"]["PlaceMedia"] after BE change
type PlaceMedia = {
  url: string;           // proxied or CDN URL preferred
  source: "wikimedia" | "osm" | "opentripmap" | "google" | "stock";
  attribution: string | null;
  width?: number;
  height?: number;
};

// PlaceOut extension OR sibling endpoint:
// Option A: PlaceOut.media?: PlaceMedia[]
// Option B: GET /api/v1/places/{id}/media → ApiResponse<PlaceMedia[]>
```

**Recommendation:** Option B first (smaller blast radius on list endpoints); fold into `PlaceOut` when stable.

---

## 4. Free providers (v1)

### 4.1 Map basemap — MapTiler (already have key)

| Style | URL pattern | Use case |
|-------|-------------|----------|
| Streets | `.../maps/streets-v2/style.json?key=` | Default, Google-like roads |
| Satellite | `.../maps/satellite/style.json?key=` | Trek / nature |
| Hybrid | `.../maps/hybrid/style.json?key=` | Labels on satellite |
| Outdoor | `.../maps/outdoor/style.json?key=` | Trails, terrain (Meghalaya) |

**Frontend-only.** No backend change.

**Env (proposed):**

```bash
# guideagent-frontend/.env
NEXT_PUBLIC_MAP_STYLE_URL=https://api.maptiler.com/maps/streets-v2/style.json?key=...
NEXT_PUBLIC_MAP_SATELLITE_STYLE_URL=https://api.maptiler.com/maps/hybrid/style.json?key=...
# optional:
NEXT_PUBLIC_MAP_OUTDOOR_STYLE_URL=https://api.maptiler.com/maps/outdoor/style.json?key=...
```

**Implementation notes (`trip-map.tsx`):**

1. Add segmented control: Map | Satellite (| Outdoor optional).
2. On change: `map.setStyle(url)` → `map.once('style.load', reAddTripLayers)`.
3. Extract layer/source setup into `attachTripGeoJson(map, geojson)` for reuse.
4. Keep list-first collapse on style failure.

### 4.2 Place images — free waterfall

| Order | Provider | Cost | Quality | Notes |
|-------|----------|------|---------|-------|
| 1 | **OSM `image` / `wikimedia` tag** on place | Free | Spotty | Parse from `Place.tags` during enrich |
| 2 | **Wikimedia Commons API** | Free | Good for famous landmarks | Search by name + bbox; store attribution |
| 3 | **OpenTripMap** place detail | Free tier | Tourism POIs | `places/xid/{xid}` preview image; need `otm:` id in tags |
| 4 | **Destination hero stock** | Free (Unsplash/Pexels API) | Generic | One hero per trip/destination only; label as stock |

**Not in v1:** Google Places Photos, Getty, scraping.

**Attribution:** Wikimedia and OTM require visible credit. Backend should normalize `attribution` string; FE shows small caption or `title` on `<img>`.

**Caching:** Store resolved URLs in DB (`places.media` JSONB column) or Redis with TTL. Proxy hotlinking through BE optional (avoids leaking keys, controls cache).

### 4.3 Rich places (non-image)

Already planned in `improve-poi-retrieval`:

- Widen Overpass tags (cafes, temples, nature, historic).
- `PLACES_SOURCES=overpass,opentripmap`.

**Hotels v1:** Do not build booking inventory. Surface:

- `accommodation_label` from generate preferences in UI.
- Optional: ingest OSM `tourism=hotel` / `guest_house` as `category=lodging` for “suggested stays” list (names only, no photos unless media enrich hits).

---

## 5. Backend changes (`guideagent`) — planned

### 5.1 New module layout (mirror `src/geo/opentripmap.py`)

```
src/geo/media/
  __init__.py          # fetch_place_media(place) facade
  schemas.py           # PlaceMedia pydantic model
  wikimedia.py
  osm_image.py
  opentripmap_preview.py
  google_places.py     # stub: raises or no-op unless key + enabled
```

### 5.2 Settings (proposed)

```bash
MEDIA_SOURCES=wikimedia,osm,opentripmap   # comma list; future: google
WIKIMEDIA_USER_AGENT=Wandr/1.0 (contact@example.com)  # required by policy
OPENTRIPMAP_API_KEY=...                   # reuse existing if OTM in PLACES_SOURCES
# Future:
GOOGLE_PLACES_API_KEY=
MEDIA_GOOGLE_ENABLED=false
```

### 5.3 Data model (proposed)

```python
# places.models.Place — add optional column:
media: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
# each entry: {url, source, attribution, width?, height?, fetched_at}
```

Alembic migration in module remote when implementing.

### 5.4 HTTP surface (proposed — module OpenSpec)

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/places/{id}/media` | On-demand resolve + cache |
| `GET /api/v1/trips/{id}/media` | Batch media for trip stops (convenience) |

Enrich script (offline):

```bash
python -m scripts.enrich_place_media --destination-id <uuid> [--limit N]
```

**Rules:**

- Fail-soft per provider (same spirit as Overpass `[]`).
- Never call media providers from `planner/service.py` generate path.
- Rate-limit Wikimedia/OTM (httpx timeouts + tenacity).

### 5.5 Google gate (future) — what changes?

| Layer | Change when adding Google |
|-------|---------------------------|
| `google_places.py` | Implement `MediaProvider.resolve(place) → list[PlaceMedia]` |
| `config.py` | `GOOGLE_PLACES_API_KEY`, append `google` to `MEDIA_SOURCES` |
| `.env.example` | Document keys + billing note |
| OpenAPI | `source` enum gains `"google"` |
| Frontend | **No structural change** — optional “Photos via Google” footer if ToS requires |
| DB / DTO | **Same** `PlaceMedia` shape |

**Estimated effort:** ~1 provider file + config + tests, not a rewrite.

---

## 6. Frontend changes (`guideagent-frontend`) — planned

### 6.1 Map basemap toggle

| File | Change |
|------|--------|
| `lib/config.ts` | `getMapSatelliteStyleUrl()`, optional `getMapOutdoorStyleUrl()` |
| `features/trips/trip-map.tsx` | Style switcher, `attachTripGeoJson` helper |
| `.env.example` | Document satellite/outdoor URLs |

**No new npm packages** (per `AGENTS.md` / `feature_ui.md`).

### 6.2 Place media consumption

| File | Change |
|------|--------|
| `lib/api/places.ts` | `getPlaceMedia(placeId)` after OpenAPI exists |
| `features/places/place-media-image.tsx` | Shared `<PlaceMediaImage>` with fallback to `categoryArt` |
| `features/trips/trip-detail.tsx` | Photo stop cards, hero (destination stock or first stop image) |
| `features/explore/feed-card.tsx` | Use shared media component when available |

**Query pattern:** TanStack Query `usePlaceMedia(placeId)` with staleTime; batch hook for trip page.

### 6.3 Guidebook UI (Layla-shaped, no PDF yet)

| Section | Source |
|---------|--------|
| Hero | Destination name + hero image (stock or best stop photo) |
| Day timeline | Existing stops + narrative + new photo cards |
| Where to stay | `trip.preferences.accommodation_label` |
| Map column | Sticky; basemap toggle |
| Export PDF | **Deferred** — print route or `@react-pdf/renderer` later |

**Typography:** already aligned in `feature_ui.md` (display font, warm paper).

### 6.4 Env (frontend)

```bash
NEXT_PUBLIC_API_URL=...
NEXT_PUBLIC_MAP_STYLE_URL=...           # street
NEXT_PUBLIC_MAP_SATELLITE_STYLE_URL=... # new
# optional NEXT_PUBLIC_MAP_OUTDOOR_STYLE_URL
```

---

## 7. Phased rollout

| Phase | Scope | Package | User-visible |
|-------|--------|---------|--------------|
| **P0** | This doc + parent OpenSpec | parent | Planning only |
| **P1** | Map street/satellite toggle | FE | Trek-friendly map |
| **P2** | Media facade + Wikimedia/OSM/OTM + `GET .../media` | BE | API ready |
| **P3** | Photo stop cards + explore cards | FE | Layla-like cards |
| **P4** | Guidebook hero + stay block | FE | Full trip polish |
| **P5** | PDF/print export | FE (+ maybe BE) | Download itinerary |
| **P6** | Google Places provider | BE | Better cafe/hotel photos |
| **P7** | Lodging search API | BE + FE | Real hotel cards |

**Suggested apply order:** P1 (FE-only) can ship before P2. P3 needs P2. Two PRs when P2+P3 land together.

---

## 8. Module OpenSpec siblings (to create on apply)

| Remote | Change name | Scope |
|--------|-------------|--------|
| parent | `free-media-map-guidebook` | Vault + boundaries (this doc) |
| guideagent | `place-media-enrich` | Media facade, DB, HTTP, scripts |
| guideagent-frontend | `map-basemap-toggle` | P1 |
| guideagent-frontend | `guidebook-trip-ui` | P3–P4 |

---

## 9. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Wikimedia rate limits / 403 | Respectful User-Agent; cache aggressively; fail-soft |
| Wrong image for ambiguous name | Prefer bbox match; require name similarity threshold |
| OTM non-commercial license | Document in `.env.example`; switch provider for commercial launch |
| MapTiler quota | Monitor; outdoor/satellite on toggle only |
| Google cost surprise | Off by default; `MEDIA_GOOGLE_ENABLED=false` |
| Generate latency regression | Hard rule: no media in SSE path (enforced in code review) |

---

## 10. Open questions (for discussion)

1. **DB column vs separate `place_media` table?** JSONB on `places` is fine for 1–3 URLs per place; table if we need history/audit.
2. **Proxy images through API?** Recommended for cache + key hiding; adds BE bandwidth.
3. **Hero image:** destination-level stock only, or best scored stop photo?
4. **Outdoor style:** third toggle or replace satellite for trek trips?
5. **PDF:** Puppeteer print page vs react-pdf — decide at P5.

---

## 11. References

- Parent OpenSpec: `openspec/changes/free-media-map-guidebook/`
- FE product UI: `guideagent-frontend/docs/feature_ui.md`
- POI facade pattern: `guideagent/openspec/changes/improve-poi-retrieval/design.md`
- Map today: `guideagent-frontend/features/trips/trip-map.tsx`
- System map: `docs/context/system-map.md`
