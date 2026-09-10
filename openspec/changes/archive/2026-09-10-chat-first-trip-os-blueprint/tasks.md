## 1. Vault paths and sibling callout

- [x] 1.1 [parent] Confirm `docs/context/README.md` and `docs/context/system-map.md` still exist; do not edit `guideagent/` or `guideagent-frontend/` application code, Compose, Dockerfiles, or run scripts
- [x] 1.2 [parent] Add a short sibling-product note to `docs/context/README.md` (contents table + warning: not Wandr generate/SSE; no invented Wandr endpoints)
- [x] 1.3 [parent] Add a short sibling-product box to `docs/context/system-map.md` pointing at the new bible file; keep existing Wandr FE↔BE map unchanged

## 2. Write the living bible

- [x] 2.1 [parent] Create `docs/context/chat-first-trip-os.md` as SSOT: product one-liner, non-goals, and principles from design D4 (structure from code, gateways, bounded tools, abort/timeout, evals/traces, step proofs)
- [x] 2.2 [parent] Document architecture (chat, TripScope, catalog acquire, travel-engine-class planner, trip artifact, explore, booking hollow) with a diagram; state stack assumption (D5) as assumption not Wandr coupling
- [x] 2.3 [parent] Document TripScope city | region | country and day-budget rules (≤3 days country → best region; longer → hub sequence + HITL; named city wins; country filter on catalog/stops) matching `adaptive-country-scope`
- [x] 2.4 [parent] Document chat 0→final loop, two compute budgets, HITL-in-chat, abortable generate, map honesty (no invented coords/polylines) matching `conversational-trip-planner`
- [x] 2.5 [parent] Document Explore dual tabs (GPS then IP; last-trip-location only after saved trip; no chat-resolve feed) matching `explore-geo-feed`
- [x] 2.6 [parent] Document booking placeholder (save without vendor; empty stays; future options keyed off saved trip location) matching `booking-placeholder`
- [x] 2.7 [parent] Add a failure-boundary table (geocoder, ingest, retrieve, LLM, routing, GPS, IP) with named fallbacks; add eval golden cases (city, region, country short vs long)
- [x] 2.8 [parent] Add phased future-build roadmap P0–P9 (foundation → chat → geo → catalog → planner → map → revision → explore → booking slot → hardening) with “proof” intent per phase; mark as **future new repo**, not this apply
- [x] 2.9 [parent] Point at Wandr method files to read (`guideagent/docs/blueprint_final.md`, `guideagent/AGENT.md`, `guideagent/docs/context.md`) and explicitly list what **not** to copy (one-hub-forever, destination_id-only retrieve as product law)

## 3. Close-out

- [x] 3.1 [parent] Re-read the four delta specs and confirm each SHALL/MUST has a matching bible section (no silent drops)
- [x] 3.2 [parent] Grep parent `docs/context/` so the bible does not invent Wandr paths/DTOs/env vars; any HTTP mentions are labeled as future-app contracts
- [x] 3.3 [parent] Do not change module OpenSpec roots, remotes, or Wandr OpenAPI as part of this change
