## Why

P5b shipped a printable guidebook from a catalog-grounded draft, but guests still cannot change that plan in chat. Without P6 the product law “make day 2 less walking updates structured itinerary + map via planning/validation, not narrative-only” stays unproven, and unbounded replan spend has no cap. P5b is complete; P6 is the next product proof.

Work type: **cross-cutting** (backend revise intent/caps/graph + reuse of generate engine + revise SSE + frontend Revise plan + goldens + Playwright/terminal validation). Not docs-only.

## What Changes

- Implement `parse_revision_intent(text, itinerary)` via `LlmGateway` role `dialogue` — structured prefs / day-constraint patches; unknown venue names ignored (never scheduled).
- Implement `ReviseCaps` / `check_caps(state)` — enforce loop, day, and walk budgets before another expensive generate; cap hit → stop and explain; keep last valid; never raise caps silently.
- Implement `revise_graph`: parse → caps → retrieve / pack / validate (reuse P4 `TravelEngine.pack` + `validate_itinerary` + narrative + `persist_draft`); greedy packer again; not LLM day order; not a new TravelEngine algorithm.
- Expose product route `POST /api/v1/sessions/{id}/revise` with `{ "text" }` — SSE progress + done/fail/aborted; same abort, disconnect, and wall-clock timeout rules as generate.
- Add FE **Revise plan** in the chat shell after a draft exists; ordinary chat send / HITL / catalog / Build plan MUST NOT start revise.
- After a successful replan, persist still requires validation; session draft + trip artifact + guidebook export + map stops update from the new structure (same `trip_id`, `status=draft`).
- Add P6.5 golden: “less walking day 2” updates structured itinerary within cap; plus unit/ASGI proofs and local terminal + Playwright/browser validation (Playwright MCP during apply).
- Follow `system-docs/phase-slices/p6-revision/` (P6.1–P6.5, guardrails, validation), `system-docs/llm.md` §7.5, `system-docs/product-goal.md` Revision, `SHARED-SWE-LLD.md`, and `SHARED-FAIL-SOFT.md`.

**Non-goals:** Unconstrained prose rewrite of the whole trip; new TravelEngine algorithm / OR-Tools / LLM stop-order; raising caps silently; booking vendor changes (P8); Explore (P7); OAuth saved-trip / save API; Wandr paths/DTOs/env; invented coords/POIs/polylines; auto-revise on every chat turn.

**BREAKING:** none for existing generate/guidebook/PDF clients beyond an additive revise route. **Spec-level:** `api-foundation` flips `POST .../revise` from non-product to product; explore/booking/trip-save remain forbidden until those slices.

## Capabilities

### New Capabilities

- `in-chat-revision`: Capped in-chat replan — structured revision intent, mandatory cap checker, `revise_graph` re-entering generate (retrieve → pack → validate → persist), revise SSE, structure+map update, less-walking-day-2 golden, explicit Revise plan CTA, Playwright/terminal proofs.

### Modified Capabilities

- `api-foundation`: Allow `POST /api/v1/sessions/{id}/revise` as a product route once this slice ships; keep explore/booking/trip-save/server-PDF non-product; revise remains in-process (Redis not required).
- `fail-soft-boundaries`: Add P6 fallbacks — loop/day/walk cap hit → stop and explain, keep last valid; replan validation fail → do not save invalid as success; unknown venues in revision text ignored; abort/timeout/disconnect share generate abort path.
- `conversational-trip-planner`: Tighten revision: after a draft exists, pace/stop/day changes MUST update structured itinerary and map via planning/validation within cap — not prose-only rewrite.
- `generate-itinerary`: Revise re-enters the existing generate pipeline (same engine, validate gate, draft persist); Build plan / chat / HITL still MUST NOT start revise; generate abort/timeout rules apply to the expensive replan run.
- `guest-chat-sessions`: After a draft exists, dialogue `POST .../messages` MUST NOT start revise; Revise plan is the explicit client replan action (same composer, dedicated route).
- `booking-placeholder`: Revise MUST NOT invent booking rates or mutate the hollow booking slot.

## Impact

- **Code / APIs:** `src/modules/agents/revise.py` (intent + graph); `src/modules/planner/caps.py`; extend pack prefs with optional per-day walk/stop overrides (no new packer); `src/api/revise.py` (or sessions); reuse `InProcessGenerateRunner` abort/timeout/SSE or a thin revise entry; `TripService.persist_draft` replace-in-place on same `trip_id`; composition-root wiring; settings `REVISE_MAX_LOOPS` (and optional `REVISE_TIMEOUT_SECONDS`).
- **Frontend:** chat shell **Revise plan** after draft; consume revise SSE; refresh session + guidebook export + MapLibre stops on `done`; abort/cap-hit honest UI; Playwright e2e for the feature.
- **Tests / CI:** unit (intent parse, cap stop+keep last valid); integration (revise_graph reuses engine; structure changes); ASGI revise SSE; golden less-walking-day-2; Playwright frontend; local terminal curl/httpx SSE smoke. Prefer fakes behind ports (no live LLM/OSRM required for green CI).
- **Docs:** implement against existing `system-docs/phase-slices/p6-revision/`; if blueprint and `llm.md` §7.5 disagree, resolve both in this change (no third shape).
- **Deps:** existing FastAPI / generate runner / TravelEngine / LlmGateway / TripService / MapLibre / Playwright stack; no new Redis requirement; no new vendor.
- **Reliability / scale (v1 posture):** cap checker before expensive generate bounds loops and spend; cooperative abort + wall-clock timeout reuse generate runner; pack/validate stay deterministic and O(n log n); same `GenerateRunner` port seam for later ARQ; replace-in-place draft avoids duplicate trip rows; routers → services → ports only.
