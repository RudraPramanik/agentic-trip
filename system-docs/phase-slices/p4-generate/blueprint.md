# P4 Generate + engine + validate — blueprint

> Status: planning blueprint (implement via later OpenSpec `p4-generate`).  
> LLD: [`../../llm.md`](../../llm.md) §7.4, §8

## Goal

GenerateRunner in-process SSE; retrieve → greedy packer → validate → narrative → session draft persist; abort on disconnect.

## Scope / modules

modules/agents/generate, planner, trips draft, GenerateRunner

## Step plan

Implement **one sub-phase at a time**.

### P4.1 — GenerateRunner + in-process SSE

- **Goal:** Port + in-process runner emitting progress events.
- **Modules:** `src/modules/agents/runner.py`
- **Types:** `GenerateRunner`, `InProcessGenerateRunner`
- **Functions:** `start(session_id)`, `abort(session_id)`
- **Services:** runner orchestrates generate service
- **Routes / APIs:** none yet
- **Algorithms / data:** cooperative `abort_requested`; **wall-clock timeout** uses the same abort path (env-tunable seconds; freeze in `p4-generate` design)
- **Depends on:** P0.4
- **Proof:** unit: start emits progress; abort **or timeout** stops further stages; no success persist after timeout
- **Non-goals:** ARQ generate adapter

### P4.2 — TravelEngine.pack

- **Goal:** Constrained greedy day-packer over catalog ids.
- **Modules:** `src/modules/planner/engine.py`
- **Types:** `TravelEngine`, `Itinerary`, `Day`, `Stop`
- **Functions:** `pack_days(scope, places, prefs) -> Itinerary`
- **Services:** planner
- **Routes / APIs:** none
- **Algorithms / data:** greedy assign under time/walk/transfer caps; hub sequence for region; O(n log n) sort + linear assign
- **Depends on:** P3.5
- **Proof:** unit: all stop ids from input places; respects day_budget length
- **Non-goals:** OR-Tools; LLM order

### P4.3 — Travel matrix

- **Goal:** Fail-soft travel times.
- **Modules:** `src/modules/planner/matrix.py`
- **Types:** `TravelMatrix`
- **Functions:** `travel_matrix(places)`, `haversine_meters(a, b)`
- **Services:** used by packer
- **Routes / APIs:** none
- **Algorithms / data:** OSRM table if present else haversine + penalty; no polyline geometry invented
- **Depends on:** P4.2
- **Proof:** unit: no OSRM → finite times; never returns fake LineString
- **Non-goals:** map drawing

### P4.4 — validate_itinerary

- **Goal:** Hard gate before persist.
- **Modules:** `src/modules/planner/validate.py`
- **Types:** `ValidateResult`
- **Functions:** `validate_itinerary(itinerary, catalog_ids, scope) -> ValidateResult`
- **Services:** planner
- **Routes / APIs:** none
- **Algorithms / data:** stop id ∈ catalog; country filter; day caps; transfer sanity
- **Depends on:** P4.2
- **Proof:** unit: unknown venue fails; foreign POI fails; cap fail
- **Non-goals:** narrative

### P4.5 — generate_graph nodes

- **Goal:** retrieve → pack → validate → narrative → persist pipeline.
- **Modules:** `src/modules/agents/generate.py`
- **Types:** generate graph state
- **Functions:** nodes calling `CatalogService.retrieve`, `TravelEngine.pack`, `validate_itinerary`, `write_narrative`, `persist_trip`
- **Services:** catalog, planner, trips, llm
- **Routes / APIs:** none
- **Algorithms / data:** no vendor HTTP in graph
- **Depends on:** P4.1–P4.4
- **Proof:** integration with fakes: valid catalog → itinerary; invalid → no persist
- **Non-goals:** media/PDF tools

### P4.6 — Narrative via gateway

- **Goal:** Titles/stories only via `LlmGateway` role `narrative`.
- **Modules:** `src/modules/planner/narrative.py` or agents
- **Types:** —
- **Functions:** `write_narrative(itinerary) -> Itinerary` (titles/stories)
- **Services:** llm port
- **Routes / APIs:** none
- **Algorithms / data:** must not add stop ids
- **Depends on:** P4.4, P0.7
- **Proof:** unit: narrative cannot introduce new place ids
- **Non-goals:** LLM stop-order

### P4.7 — Draft persist

- **Goal:** Persist session **`draft`** only if validation passed. Not a saved trip.
- **Modules:** `src/modules/trips/`
- **Types:** `TripService`, draft trip row (`status=draft`)
- **Functions:** `TripService.persist_draft(session_id, itinerary, validation)`
- **Services:** `TripService`
- **Routes / APIs:** none yet
- **Algorithms / data:** refuse if validation fail unless aborted; do **not** set `saved` or add a save API
- **Depends on:** P4.5, P1.2
- **Proof:** unit: fail validation → no success persist; success → `status=draft` (last-trip still locked)
- **Non-goals:** OAuth saved trip (auth later); booking vendors; save API

### P4.8 — Abort

- **Goal:** Disconnect + explicit abort.
- **Modules:** runner + `src/api/`
- **Types:** —
- **Functions:** `GenerateRunner.abort`; set `run.abort_requested` (disconnect, explicit abort, **or wall-clock timeout**)
- **Services:** runner
- **Routes / APIs:** `POST /api/v1/sessions/{id}/generate/abort`
- **Algorithms / data:** cooperative cancel; no unbounded continuation; timeout → same path, honest SSE `aborted` or `error`
- **Depends on:** P4.1
- **Proof:** abort test: no further LLM/engine after abort; timeout test: no success persist
- **Non-goals:** HITL interrupt (different)

### P4.9 — Generate HTTP SSE

- **Goal:** Start generate with progress SSE.
- **Modules:** `src/api/generate.py`
- **Types:** SSE `progress` | `done` | `error` | `aborted`
- **Functions:** `start_generate()` router
- **Services:** `GenerateRunner`
- **Routes / APIs:** `POST /api/v1/sessions/{id}/generate`
- **Algorithms / data:** —
- **Depends on:** P4.5, P4.8
- **Proof:** ASGI SSE progress then done/fail
- **Non-goals:** Wandr generate paths

### P4.10 — Generate goldens

- **Goal:** Meghalaya/Japan-shaped structured days; catalog-only stops.
- **Modules:** `tests/evals/`
- **Types:** fixtures
- **Functions:** golden asserts
- **Services:** —
- **Routes / APIs:** —
- **Algorithms / data:** —
- **Depends on:** P4.9
- **Proof:** goldens: Meghalaya/Japan-shaped catalog-only days; Japan-10-days-or-HITL; border/country filter; abandoned generate; failed generate still traced (obs fake or no-op)
- **Non-goals:** PDF/map UI

### P4.11 — FE generate CTA

- **Goal:** After `trip_scope` is confirmed, chat shows an explicit **Build plan** control that calls existing `POST /api/v1/sessions/{id}/generate`. Confirming scope does not start generate.
- **Modules:** `frontend/` chat (depends on P1.8 shell; P1.8 still has no generate button)
- **Types:** `GenerateCta`
- **Functions:** `startGenerate(session_id)` → existing generate SSE
- **Services:** none (client)
- **Routes / APIs:** consumes P4.9
- **Algorithms / data:** —
- **Depends on:** P4.9, P2.7, P1.8
- **Proof:** documented: scope confirm waits; CTA starts generate SSE; dialogue message does not
- **Non-goals:** new HTTP resource; auto-generate on confirm_scope

## Proof

Meghalaya/Japan-shaped generate produces structured days with catalog-only stops; abort/timeout stops work; Build plan CTA is explicit

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
