## Why

P3 shipped grounded catalog acquire/retrieve (PostGIS places, readiness, country filter), but the product still cannot turn a confirmed `trip_scope` + catalog into a structured multi-day itinerary. Without P4 there is no GenerateRunner, greedy packer, hard validate gate, draft persist, abort/timeout, generate SSE, or explicit **Build plan** CTA — so the core “structure from code, narrative from LLM” loop remains unproven. P3 is archived complete; P4 is the next product proof.

Work type: **cross-cutting** (backend planner/agents/trips + API SSE + frontend Build plan CTA + tests/evals + local browser/terminal validation). Not docs-only.

## What Changes

- Implement `GenerateRunner` / `InProcessGenerateRunner` with cooperative `abort_requested`, wall-clock timeout (env-tunable), and progress emission for SSE.
- Implement `TravelEngine.pack` (constrained greedy day-packer over catalog place ids) and `travel_matrix` / `haversine_meters` (OSRM table if present else haversine + penalty; never fake polylines).
- Implement pure `validate_itinerary` hard gates (stop id ∈ catalog, country filter, day caps, transfer sanity) before any success persist.
- Wire `generate_graph`: retrieve → pack → validate → narrative (`LlmGateway` role `narrative`) → `TripService.persist_draft` (`status=draft` only).
- Expose product routes: `POST /api/v1/sessions/{id}/generate` (SSE `progress` | `done` | `error` | `aborted`) and `POST /api/v1/sessions/{id}/generate/abort`.
- Add FE **Build plan** CTA after `trip_scope` is confirmed; confirming scope / chat / HITL MUST NOT start generate.
- Add generate goldens (Meghalaya/Japan-shaped catalog-only days; Japan-10-days-or-HITL; border/country filter; abandoned generate; failed generate still traced) plus local terminal + browser validation.
- Follow `system-docs/phase-slices/p4-generate/` (P4.1–P4.11, guardrails, validation), `system-docs/llm.md` §7.4 / §8, `SHARED-SWE-LLD.md`, and `SHARED-FAIL-SOFT.md`.

**Non-goals:** ARQ generate adapter; OR-Tools / LLM stop-order; map/guidebook/PDF UI (P5/P5b); revise (P6); Explore (P7); booking (P8); OAuth saved trip / save API; Wandr paths/DTOs/env; invented coords/POIs/polylines; auto-generate on confirm_scope.

**BREAKING:** none for existing dialogue/catalog clients beyond additive generate routes. **Spec-level:** `api-foundation` flips generate (+ abort) from non-product to product for this slice; trip/explore/booking remain forbidden until their slices.

## Capabilities

### New Capabilities

- `generate-itinerary`: Abortable in-process generate pipeline — retrieve → greedy pack → validate → narrative → session draft persist; TravelEngine + travel matrix; GenerateRunner port; generate SSE + abort HTTP; wall-clock timeout; eval goldens; explicit Build plan CTA.

### Modified Capabilities

- `api-foundation`: Allow `POST /api/v1/sessions/{id}/generate` and `POST /api/v1/sessions/{id}/generate/abort` as product routes once this slice ships; keep trip/explore/booking non-product; generate remains in-process (Redis not required for generate).
- `fail-soft-boundaries`: Tighten P4 generate/routing/narrative/abort fallbacks — validation fail → no success persist; narrative fail → never invent stops; routing missing → haversine times, no fake geometry; abort/timeout → cooperative cancel, honest SSE; empty retrieve at generate → honest fail/HITL path, no invented venues.
- `guest-chat-sessions`: After successful generate, session projection MAY surface draft itinerary summary; chat/HITL/scope confirm MUST still NOT start generate; Build plan is the explicit client action.
- `conversational-trip-planner`: Clarify that v1 successful generate persists `status=draft` (reopenable in guest session) and that structure/validate/timeout/explicit-action laws are owned by the generate pipeline in this slice.
- `adaptive-country-scope`: Reinforce that packing/validation apply hub-sequence / country-long day-budget rules and country filter on scheduled stops (Japan-10-days-or-HITL golden).

## Impact

- **Code / APIs:** `src/modules/agents/runner.py`, `generate.py`; `src/modules/planner/` (engine, matrix, validate, narrative); `src/modules/trips/` (`TripService.persist_draft`); `src/api/generate.py`; port implementations for `GenerateRunner` / `TravelEngine`; composition root wiring; Alembic draft-trip persistence if needed.
- **Frontend:** chat shell **Build plan** CTA consuming generate SSE + abort; no auto-start on scope confirm.
- **Tests / CI:** unit (packer, matrix, validate, narrative id lock, runner abort/timeout); integration with fakes (graph persist rules); ASGI SSE generate/abort; goldens under `tests/evals/`; local browser + terminal smoke documented in tasks. Prefer fakes behind ports (no live OSRM/LLM required for green CI).
- **Docs:** implement against existing `system-docs/phase-slices/p4-generate/`; if blueprint and `llm.md` disagree, resolve both in this change (no third shape).
- **Deps:** existing FastAPI/SQLAlchemy/PostGIS/ObsPort/LlmGateway/CatalogService stack; optional OSRM for matrix (fail-soft without it); no new Redis requirement for generate.
- **Reliability / scale (v1 posture):** cooperative cancel + wall-clock timeout bound spend; pure pack/validate keep CPU work deterministic and testable; in-process runner with port seam for later ARQ; draft-only persist avoids premature saved-trip coupling; catalog-id-only stops keep grounding enforceable at scale.
