## Why

Wandr is a strong **search-then-plan** product (pick a city hub, prepare a radius catalog, generate). We want a **separate** conversational trip OS — Layla-shaped from first chat turn to a saved, map-backed itinerary — where the user prompts a country, region, or place and the system resolves geography, decomposes by day budget, and plans. This change captures the platform bible in parent docs so a new app can be built later without forking Wandr remotes.

## What Changes

- **Work type: parent-context-only.** Planning and vault docs live under `tripplanner/docs/context/` (and this OpenSpec change). No `guideagent/` or `guideagent-frontend/` application code in this change. New product code ships later in its own repos; this bible is a seed to **replace/move** then.
- **Product bible:** Multi-step blueprint (principles, geo model, chat loop, map artifact, explore, booking hollow, AI-systems guardrails, phased build + proofs) modeled on Wandr’s method (`blueprint_final` + `context.md` + `AGENT.md` + step proofs), not on Wandr’s one-hub intake.
- **Chat-first planner:** User prompt is the intake. LLM + tools resolve **one** city, region, or country (HITL when ambiguous or oversized). Output is a day-by-day trip with map polylines/guidebook, then revision in chat.
- **Adaptive country trips:** Country is a first-class prompt (many users will type a country). Short schedules (e.g. ~3 days) stay in the **best region** of that country. Longer schedules select **best places/hubs** that fit total days (HITL when the choice is material). Single-hub compact loops remain the city-scale path.
- **Explore:** Location feed with two subtabs. **Near me** uses device GPS with **IP** fallback. **Last search / last trip location** exists only **after a saved trip** — not from mid-chat geo resolve.
- **Booking:** Out of v1 fulfillment. UI may show an empty stays slot (or later hotels keyed off the **saved trip** location).

### Non-goals

- Extending Wandr compose/generate into a chat client, or merging this product into `guideagent` / `guideagent-frontend` remotes.
- Inventing Wandr endpoints, DTO fields, or env vars; do not change Wandr OpenAPI.
- Human travel-agent ops, live flight booking, or paid lodging checkout in this bible’s v1.
- Polygon-perfect political GIS; social graph (likes/follows/stories).
- Merging remotes, parent docker-compose, relocating module OpenSpec, or changing module Compose/Dockerfiles/run scripts.
- Implementing the new application in this change (docs/bible only).

## Capabilities

### New Capabilities

- `conversational-trip-planner`: Chat is intake through saved itinerary and revision; streaming dialogue vs expensive generate; map-day artifact; HITL in conversation.
- `adaptive-country-scope`: Resolve city | region | country; day-budget decomposition (short stay → best region; longer → best hubs/places + HITL); catalogs stay in resolved country.
- `explore-geo-feed`: Dual-tab location explore — GPS/IP near-me always; last-trip-location tab only after a saved trip.
- `booking-placeholder`: Empty or later stays options keyed off saved trip location; no booking vendor required.

### Modified Capabilities

- (none — parent `openspec/specs/` today covers Wandr cross-boundary contracts only; this is a new product bible, not a delta on Wandr hub-intake or polyline boundaries)

## Impact

- **Parent (`docs/context/`):** Add a living blueprint (and a short system-map pointer) for the new conversational trip OS. Agents use it as SSOT until a new repo replaces it.
- **This OpenSpec change:** Specs + design + phased tasks for writing that bible. Apply = documentation only.
- **Wandr modules:** Unchanged. Patterns to **learn from** (not call): `guideagent/docs/blueprint_final.md` principles, `travel_engine` purity, phase-gated tools, SSE abort, evals/Langfuse, MapLibre GeoJSON honesty, Explore immersion UX.
- **Future new app:** Separate remotes; stack assumed FastAPI modular monolith + Next.js + PostGIS + Qdrant + LiteLLM/LangGraph + MapLibre unless a later design revises it. Shared packages with Wandr are optional and not a day-one constraint.
- **APIs:** None in Wandr. New product contracts are specified here as **behavior**, not as invented Wandr OpenAPI.
