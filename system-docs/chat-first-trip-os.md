# Chat-first trip OS — living bible

> **Status:** Product bible SSOT for **agentic-trip** (not Wandr).  
> **OpenSpec root:** this repo — `openspec/` (main specs seeded from archived `chat-first-trip-os-blueprint`).  
> **Agents:** This file is **not** Wandr generate/SSE. Do **not** invent Wandr OpenAPI paths, DTOs, or env vars from this bible.

---

## Product one-liner

A conversational trip OS: the user prompts a country, region, place, or vibe in chat; the system resolves geography, plans a grounded multi-day itinerary with a map, allows in-chat revision, and offers location-based Explore. Booking is optional and hollow in v1.

Layla-shaped **from first chat turn to a saved trip**. Not a chat skin on Wandr’s search-then-compose flow.

---

## Non-goals

- Extending Wandr compose/generate into this product, or merging remotes
- Human travel-agent ops, live flight GDS, or paid lodging checkout in v1
- Polygon-perfect political GIS; likes/follows/stories
- Parent docker-compose; relocating module OpenSpec; changing Wandr Compose/Dockerfiles/run scripts
- Inventing Wandr endpoints from this document

---

## Principles (steal Wandr *laws*, not Wandr *intake*)

1. **Structure from code, narrative from the language model.** Day structure, stop order, visit windows, and coordinates never come from unconstrained model prose. Models may parse prefs and write titles/stories.
2. **Single LLM gateway; single geo gateway.** No scattered vendor SDKs.
3. **Phase-gated typed tools; bounded loops; validate before finish.** No unbounded ReAct. Finish/save must not succeed if itinerary validation failed (unless the run was explicitly aborted).
4. **Stream abort on disconnect; generation timeout.** Leaving the client must stop expensive generate work.
5. **Eval harness + fail-soft tracing from day one.** Every generate/material replan is traceable; evaluation is recorded even on partial failure.
6. **Packages at point of use; every future phase ends with a runnable proof.**
7. **Lean agent checkpoint in the future repo** (`context.md` style). Until then, this file is the fat bible.

A language-model-named venue that is **not** in the retrieved catalog is **not** scheduled. Coordinates and polylines are never invented to look nicer.

---

## Architecture

**Stack (see also `system-docs/architecture-draft.md` — settled):** FastAPI modular monolith at repo root (`/src`) + Next.js (`/frontend`) + PostGIS (+ Qdrant later) + LiteLLM multi-model gateway + LangGraph + ARQ/Redis for long jobs + MapLibre + guest cookie session (OAuth later). Phase delivery via `phase-slices/`. Shared libraries with Wandr are optional and post-v1.


**Auth / save:** Guests may chat, HITL, and generate a session draft without a login wall. **Persisting a saved trip** and **saving explore places** require an authenticated user (OAuth later). Explore **Last trip location** remains only after a **saved** trip.

**LLM:** Single `LlmGateway` (LiteLLM). Role aliases (`dialogue`, `narrative`, `embed`) map to Bedrock / Gemini / OpenRouter / NIM (or others) via env — no scattered vendor SDKs.

**Generate:** Abortable streaming progress (`GenerateRunner`); default in-process SSE; ARQ adapter later. Catalog acquire may use ARQ earlier.

```
                    ┌─────────────┐     ┌─────────────┐
                    │  Chat UI    │     │   Explore   │
                    │  Map canvas │     │ Near me     │
                    │  Guidebook  │     │ Last trip*  │
                    └──────┬──────┘     └──────┬──────┘
                           │                   │
                    ┌──────▼───────────────────▼──────┐
                    │         Orchestrator            │
                    │  dialogue vs generate budgets   │
                    └──────┬──────────────────────────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │ Geo tools  │  │ Catalog    │  │ Travel     │
    │ gazetteer  │  │ acquire +  │  │ engine     │
    │ confirm    │  │ retrieve   │  │ schedule / │
    └────────────┘  └────────────┘  │ route /    │
                                    │ validate   │
                                    └─────┬──────┘
                                          ▼
                               ┌──────────────────┐
                               │ Trip artifact    │
                               │ days, map, stays │
                               │ placeholder      │
                               └──────────────────┘
```

\* Last trip location Explore exists only after a **saved** trip.

Future-app HTTP is **not** Wandr OpenAPI. Do not reuse or invent `guideagent` routes here.

---

## TripScope and day budget

Each planning session resolves to **exactly one** scope kind: `city` | `region` | `country`. Geo tools (gazetteer/geocoder class) confirm identity and coordinates. The language model is **not** the sole source of truth for admin identity. Ambiguous matches HITL in chat — never silently centroid-plan a country.

**Geo signals first, model second.** Oversized vs city-scale uses deterministic metadata (admin level, bbox span, place class) before any hub-suggestion model call. A clearly city-scale geocode does **not** require a hub-suggestion model call. Thin country metadata may use a model to suggest hubs, then **tools + HITL** as below.

| Kind | Planning shape |
|------|----------------|
| **City** | Single planning base; compact multi-day loop. Do not force a country-wide hub list. |
| **Region** | Stay inside that region (bbox / hubs). Not an arbitrary country centroid. |
| **Country + ≤3 days** (default short threshold; tunable later) | **One best region** of that country — not a nationwide hop. Chat states which region and why (high level). |
| **Country + longer** | **Best hub/place sequence** that fits total days. HITL if alternatives are similarly reasonable or a transfer would consume a full day. |

**Named city or region always wins.** If the user asked for 3 days **and** named a city, that city is the scope — do not override with a different “best region.”

**“Best”** = grounded catalog quality + travel compactness + preference fit — not unconstrained model geography. Day structure still comes from the planning engine, not a free-form city list in prose.

**Country trips are not a country-centroid radius scrape.** Ingest the chosen region or hubs only. Honesty if the catalog is thin.

**Country filter:** ingested/retrieved places and scheduled stops MUST belong to the resolved country. Border-adjacent catalogs MUST NOT schedule foreign POIs. Unknown-country POIs near a border are **excluded**, not guessed in.

---

## Chat 0 → final

Guests can start without a login wall. Chat is the **only** required intake: no destination typeahead as a mandatory first step.

```
1. Open chat (guest ok)
2. Prompt anything (country / region / place / vibe)
3. Cheap dialogue: intent + geo candidates + HITL if needed
4. Explain chosen TripScope in the conversation
5. Explicit expensive generate: catalog → retrieve → engine → validate → narrative
6. Persist trip artifact (ordered days, real place ids + coords)
7. Map: stops always; road polylines only when routing geometry exists
8. Revise in chat (capped loops; structure via engine, not prose rewrite)
9. Reopen later: same days + mapped stops
```

### Two compute budgets

| Turn | Job | Rule |
|------|-----|------|
| **Dialogue** | Intent, clarification, HITL, explain scope | Cheap; **not** a saved itinerary. Ambiguous “Paris” → candidates in chat, wait. Missing duration → ask, do not persist a trip. |
| **Generate / replan** | Acquire catalog, retrieve, travel-engine-class plan, validate, narrative | Expensive, traced, **abortable** on disconnect/cancel. Must not run on every chat message. |

HITL stays **in the same chat** (candidates, hub/region chips). It is not a separate search-first page as the only path. For country prompts, the system may ask a short HITL **or** apply the day-budget default — and **must** explain the chosen scope.

**Save integrity:** if validation of day caps, travel, or catalog grounding fails and the run was not aborted, do **not** persist a successful trip. Failed/clarification generates still record observability outcome and evaluation (fail-soft tracer if unconfigured).

**Revision:** “make day 2 less walking” updates structured itinerary + map via planning/validation, not narrative-only. Unbounded revision loops are capped.

---

## Explore

Two subtabs (wording may vary). Switching does **not** destroy the other tab’s anchor. Feeds are real catalog places — no invented venues or coordinates. Instagram-like masonry is allowed.

| Tab | Anchor | Rules |
|-----|--------|--------|
| **Near me** | Device GPS, then **IP** if GPS denied/unavailable/timeout | Approximate copy for IP. If **both** fail: honest empty/error + retry — **never** fake a city. Independent of trips. |
| **Last trip location** | Geography of a **persisted** trip (default: **latest saved**) | Empty/locked until a trip is saved. Chat geo-resolve, HITL pick, or unsaved draft MUST NOT fill this tab. Optional pin of an older saved trip later; default is latest. |

Wandr Explore today has **no** nearby HTTP. This product **does** need a real nearby query in the **future app** — that is not Wandr `places?destination_id=`. Do not pretend Wandr’s catalog feed is this contract.

**Honesty:** category/stock art is not a venue photo unless a real place-media URL exists. No likes/follows/stories in v1. A card may start/continue planning with that place’s **real** identity (no fake ids). Cards are not itinerary stops — do not treat them as day-edit mutations.

---

## Booking (hollow)

The user can **save and view** a planned itinerary with map days **without** any booking. v1 does not block on lodging or flight vendors.

The trip UI **may** show an empty stays/booking block (“coming later”). No invented live prices, availability, or fake reservations.

**Later** hotels/options (if added) key off the **saved trip** location/region — not GPS, IP, or unsaved chat resolve. Until a trip is saved, do not present hotels as belonging to “this trip.” Near-me lodging is a separate explicit user action, not the default trip-keyed list.

---

## Failure boundaries

Every external kind has a named fallback. Never let an upstream failure become an unbounded hang or a hallucinated map.

| Kind | Failure | Fallback |
|------|---------|----------|
| Geocoder / gazetteer | Timeout, empty, ambiguous | Dialogue HITL; do not centroid-plan a country |
| Ingest / catalog acquire | Thin region, source down | Honest readiness; do not refill from a foreign country |
| Retrieve | Empty index | Geo fallback search inside scope; if still empty, say so and HITL |
| LLM | Parse fail, tool-loop cap | Defaults where safe; force wrap-up/validate; never invent coords |
| Routing | No geometry / provider down | Times via fail-soft matrix; map **points only** (no fake polylines) |
| GPS | Deny / timeout | IP approximate for Near me |
| IP | Lookup fail | Honest empty Near me + retry; never fill Last trip location from IP |

---

## Eval goldens (before calling the planner production-quality)

Harness cases the future repo MUST include:

| Case | Expect |
|------|--------|
| City (“Kyoto, 4 days, food”) | City scope; compact loop; no country-wide hubs required |
| Region (“Tuscany, 5 days, wine”) | Region scope; not a Italy centroid |
| Country short (“Japan, 3 days”) | Single **best region**; chat names it; no nationwide hop |
| Country short + named city (“3 days in Kyoto”) | City wins; no override region |
| Country long (“Japan, 10 days, slow”) | Hub sequence fitting ~10 days, or HITL between few coherent alternatives |
| Ambiguous (“Paris”) | HITL candidates; no silent country pick |
| Border city | Stops only in resolved country |
| Missing duration | Dialogue ask; no trip persist |
| Abandoned generate | Work stops; no unbounded spend |

Traces: generate, error, and clarification outcomes still recorded.

---

## Future-build roadmap (new repo — not this apply)

Implement in a **future new OpenSpec root / remotes**. This vault apply does **not** start that code.

| Phase | Ships | Proof intent |
|-------|--------|----------------|
| **P0** Foundation | Principles, AGENT.md, repo layout, obs/evals skeleton, health | Health endpoint + empty shell |
| **P1** Chat | Session, streaming, guest cookie | Round-trip message |
| **P2** Geo | Intent schema + TripScope + HITL in chat | Goldens: city / region / country / ambiguous |
| **P3** Catalog | Acquire by chosen region/hubs (never country centroid scrape) | Honest readiness floor |
| **P4** Planner | Travel-engine-class behind generate budget | Itinerary; no invented coords; validation gate |
| **P5** Map + guidebook | Days + points; polylines when routing exists; **export DTO** | Reopenable artifact |
| **P5b** PDF/print | Export from guidebook DTO | Download/print |
| **P6** Revision | Chat edits, capped replans | Structure+map update; eval flag |
| **P7** Explore | Dual-tab nearby (GPS→IP; last trip after save) | No fake POIs; last-trip locked pre-save |
| **P8** Booking slot | Empty stays; save without vendor | No fake rates |
| **P9** Hardening | Eval gate, cost caps, abort, rate limits | Golden harness pass |
| **Later** | OAuth save, media, Qdrant, ARQ generate adapter, booking adapters | Facades |

---

## Learn from Wandr — method, not product law

**Read for how to build a platform (do not import as this product’s intake):**

- `guideagent/docs/blueprint_final.md` — principles, failure tables, step proofs
- `guideagent/AGENT.md` — hard coding guardrails (gateways, purity, bounds)
- `guideagent/docs/context.md` — lean agent checkpoint pattern

**Do not copy as product law:**

- One hub forever after HITL (Wandr deferred multi-hub stitching; this OS plans country/region by day budget)
- Retrieve filtered **only** by a single city `destination_id` as the only legal catalog scope
- Country prompt collapsing to a country-centroid radius scrape
- Explore as destination-catalog-only with GPS as a mock (this OS needs real nearby + IP, and last-trip only after save)
- Search-first typeahead as required intake before chat

Wandr remains the shipped city-hub planner. This bible is the sibling OS until it lives in its own repo.
