## Context

See `proposal.md` for motivation. Wandr (`guideagent` + `guideagent-frontend`) is a search-first, **one `destination_id`**, radius-prepare planner. Its method is documented in `guideagent/docs/blueprint_final.md` (principles, failure boundaries, step proofs), `guideagent/docs/context.md` (agent checkpoint), and `guideagent/AGENT.md` (hard rules). Parent vault: `docs/context/system-map.md` (Wandr FE↔BE only).

This change does **not** modify Wandr routers or OpenAPI. Apply writes a living bible under `docs/context/` so a **new** product can be built later in separate remotes. Specs under this change are the behavior contract that bible MUST encode.

## Goals / Non-Goals

**Goals:**

- Encode architecture, AI-systems guardrails, geo/explore/booking decisions, and a phased build-with-proofs plan in parent docs.
- Make the bible usable as Wandr-style agent SSOT (principles + phases + failure table + “next step”) without copying module AGENT.md verbatim.
- Keep Wandr running and untouched.

**Non-Goals:**

- Scaffolding new git remotes, Docker, or package run scripts in this change.
- Porting Wandr compose/generate HTTP into a chat client.
- Choosing a booking vendor or live flight GDS.
- Exact numeric radius/top_k/timeouts for the new app (copy Wandr *kinds* of contracts; tune at implementation).

## Decisions

### D1 — Parent vault is the temporary SSOT; new repo replaces it

**Choice:** Apply this change by adding `docs/context/chat-first-trip-os.md` (the bible) and a short pointer in `docs/context/README.md` and `docs/context/system-map.md` (sibling product, not Wandr traffic). Do not relocate `guideagent` OpenSpec or merge remotes.

**Why:** User asked the bible to live in Wandr docs until build starts.

**Alternatives:** New OpenSpec store/repo now (cleaner long-term, extra ceremony); put the bible only inside this change folder (agents on parent `docs/context` would miss it).

### D2 — TripScope + day-budget decomposition (not Wandr one-hub)

**Choice:** First-class `TripScope` `{ kind: city | region | country, geo identity from tools, day_budget }`.

| Kind | Planning shape |
|------|----------------|
| City | Single base, compact multi-day loop (Wandr-like *shape*) |
| Region | Bbox/hubs inside the region |
| Country + ≤3 days (default short threshold) | **One best region** of that country |
| Country + longer | **Best hub/place sequence** that fits total days; HITL if alternatives are close or transfers eat a day |

“Best” = grounded catalog + compactness + preference fit, confirmed by geo tools. Geo metadata classifies scale before any hub-suggestion LLM call (same *idea* as archived parent `search-first-hub-planning` D2, but country trips are in scope here).

**Why:** Users will type countries; a 3-day Japan trip must not become a nationwide hop; a 10-day trip must not pretend one city disk is the country.

**Alternatives:** Always HITL a single city (honest but not a Layla-like 0→final); always multi-city even for 3 days (exhausting, bad travel math).

### D3 — Two compute budgets in one chat session

**Choice:**

- **Dialogue:** parse intent, HITL, explain scope — cheap, frequent, streaming tokens.
- **Generate/replan:** catalog acquire → retrieve → deterministic travel engine → validate → narrative — expensive, abortable, traced.

Do not invoke generate on every user message. Clarification is a successful dialogue outcome, not a failed generate.

**Why:** Cost, latency, and Wandr’s lesson that unbounded tool loops need caps.

**Alternatives:** One mega-agent every turn (costly, flaky); form-based compose after chat resolve (not 0→final clone).

### D4 — Steal Wandr laws, not Wandr intake

**Choice:** Bible principles MUST include:

1. Structure from code; narrative from LLM; never invent coords / stop order / times  
2. Single LLM gateway; single geo gateway  
3. Phase-gated typed tools; bounded loops; validate before finish  
4. SSE/stream abort on disconnect; generation timeout  
5. Eval harness + fail-soft tracing from day one  
6. Packages at point of use; every phase ends with a runnable proof  
7. Lean agent `context.md` in the **future** repo; fat bible stays one file until then  

Do **not** copy Wandr’s `destination_id`-only Qdrant filter or “HITL then one hub forever” as product law.

**Why:** Those laws are why Wandr itineraries are map-trustable. The new geo model is the product delta.

**Alternatives:** Prompt-only itineraries (map trust dies); shared npm/Python packages on day one (couples two products).

### D5 — Stack assumption until a later repo design revises it

**Choice:** Document the default as FastAPI modular monolith + Next.js + PostGIS + Qdrant + LiteLLM + LangGraph + MapLibre + cookie session (guest + later OAuth). Call it an assumption, not a Wandr dependency. Shared libraries with Wandr are optional and post-v1.

**Why:** Team already knows this machine; bible phases map cleanly onto it.

**Alternatives:** Python-only; serverless chat; different vector DB — allowed later if the new repo design changes D5 without changing specs.

### D6 — Explore anchors

**Choice:**

- **Near me:** GPS, then IP; honest empty if both fail. Requires a **real nearby** query in the new app (Wandr Explore correctly has no nearby API today — do not pretend Wandr `GET /places?destination_id=` is this feed).
- **Last trip location:** only after a **saved trip**; default = latest saved trip scope. Chat resolve / HITL MUST NOT write this tab.

**Why:** User constraint: no last-search from unsaved chat; location/IP only until a trip exists.

**Alternatives:** Session last-geocode (rejected); GPS-only with no IP (worse empty rate).

### D7 — Booking hollow

**Choice:** Trip complete without vendors. Optional empty stays block. Future hotels/options keyed off **saved trip** location only.

**Why:** Specs `booking-placeholder`. Keeps v1 an itinerary OS.

### D8 — Bible document shape (what apply writes)

**Choice:** One SSOT markdown: `docs/context/chat-first-trip-os.md` with:

- Product one-liner + non-goals  
- Principles (D4)  
- Architecture diagram (chat / scope / catalog / engine / artifact / explore)  
- TripScope + day-budget table (D2)  
- Chat 0→final loop + two budgets (D3)  
- Explore + booking (D6–D7)  
- Failure boundary table (kinds: geocoder, ingest, retrieve, LLM, routing, GPS, IP)  
- Phased build P0–P9 matching tasks in this change (docs now; code later in new repo)  
- Pointers to Wandr files to **read for method**, not to import  

Short “sibling product” note in `docs/context/README.md` and `docs/context/system-map.md` so agents do not treat the bible as Wandr generate/SSE.

**Why:** Mirrors `blueprint_final.md` as SSOT without forking backend docs.

**Alternatives:** Split into many files immediately (harder to replace when the new repo starts).

### D9 — Apply vs later implementation

**Choice:** Tasks in this change are **parent-doc** tasks only. Implementing the app is a future OpenSpec root. Do not add guideagent/frontend tasks that edit product code.

**Why:** Planning boundary + user: replace docs when build starts.

## Risks / Trade-offs

- **[Risk] Agents confuse this bible with Wandr generate** → Mitigation: system-map sibling callout; explicit “do not invent Wandr endpoints”; AGENTS.md left as Wandr router unless a later tiny pointer is wanted (optional; default: README + system-map only).
- **[Risk] “Best region” is subjective / biased to tourist defaults** → Mitigation: spec requires grounded catalog + compactness; eval goldens for short country stays; HITL when scores are close.
- **[Risk] Country ingest cost (Japan-scale scrape)** → Mitigation: never centroid-scrape a country; ingest the chosen region or hubs only; readiness honest if catalog thin.
- **[Risk] IP geolocation is coarse / wrong country** → Mitigation: Near me copy as approximate; user can retry GPS; never use IP to fill Last trip location.
- **[Risk] 3-day threshold is wrong for islands vs continents** → Mitigation: default 3; bible allows tuning; user-named city/region always wins.
- **[Trade-off] Docs-only apply means no running chat yet** → Accepted; this change is the bible.
- **[Trade-off] Greenfield vs Wandr fork** → Accepted duplication of patterns; avoids coupling remotes.

## Migration Plan

1. Merge this OpenSpec change’s docs into parent `docs/context/` (apply).
2. Use the bible in explore/propose sessions for the new app; do not implement inside Wandr modules.
3. When the new repo exists: copy/adapt the bible into that repo’s `docs/`, point parent README to the new home, then archive or shrink the parent copy.
4. Rollback: delete the sibling docs; Wandr unchanged.

## Open Questions

- Exact short-stay threshold for tiny countries (tune at implementation; default 3 days stands).
- Whether Last trip location can pin an older saved trip (optional; default latest saved).
- Brand/name of the new app (not required to write the bible).
