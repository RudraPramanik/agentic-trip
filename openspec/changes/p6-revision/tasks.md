## 1. Settings + RevisionIntent parse (P6.1)

- [ ] 1.1 backend: Add `REVISE_MAX_LOOPS` (default 3) and `REVISE_TIMEOUT_SECONDS` (default 120) to Settings; document names only in `.env.example` / `.env.demo` (no secrets)
- [ ] 1.2 backend: Add `RevisionIntent` + `parse_revision_intent(text, itinerary)` in `src/modules/agents/revise.py` via `LlmGateway` role `dialogue` (schema-first patch: day_index, walk/stop budgets, drop_place_ids only if already on itinerary); unknown venue names ignored; heuristic fail-soft for “less walking” + optional “day N” when LLM unavailable
- [ ] 1.3 backend: Proof — unit: “less walking day 2” → day-2 walk/stop-cap patch; unknown venue name not scheduled; no whole-trip prose rewrite

## 2. Cap checker (P6.2)

- [ ] 2.1 backend: Implement `ReviseCaps` + `check_caps(state)` in `src/modules/planner/caps.py`; snapshot baseline walk/day/stop budgets on first successful generate; count failed attempts toward the loop budget; refuse silent cap raises
- [ ] 2.2 backend: Proof — unit: loop cap → `StopAndExplain` and last valid itinerary unchanged; patch that would raise walk/day budgets is refused

## 3. Per-day pack prefs + revise_graph (P6.3)

- [ ] 3.1 backend: Extend `pack_days` prefs with optional `day_overrides` (max_stops / travel budget per day_index); default pack path unchanged; no new TravelEngine algorithm
- [ ] 3.2 backend: Implement `run_revise`: parse → caps → merge prefs → reuse `run_generate` stages (retrieve → pack → validate → narrative → persist_draft); services/ports only; same `trip_id` / `status=draft`; booking slot stays hollow
- [ ] 3.3 backend: Proof — integration with fakes: valid walk-cap patch changes structured day 2; validation fail does not persist success; last valid kept; export/map stop ids follow the new structure

## 4. Revise HTTP SSE + runner (P6.4)

- [ ] 4.1 backend: Extend `InProcessGenerateRunner` with `start_revise(session_id, text)` (same abort flag, watchdog, SSE queue); refuse concurrent generate+revise on one session; timeout shares abort path
- [ ] 4.2 backend: Add `src/api/revise.py` `POST /api/v1/sessions/{id}/revise` `{ "text" }` SSE (`progress` | `done` | `error` | `aborted`); ownership checks; no-draft honest error; disconnect → abort; mount router; reuse `POST .../generate/abort` for in-flight revise (optional `/revise/abort` alias only if needed)
- [ ] 4.3 backend: Proof — ASGI: progress then done; cap-hit error keeps last valid; abort/timeout keeps last valid; foreign session denied; Redis down does not block revise

## 5. Less-walking-day-2 golden (P6.5)

- [ ] 5.1 backend: Add `tests/evals/` golden: less walking day 2 updates structured itinerary within cap; validation still required to persist; failed/capped revise still traced (fake Obs) or no-op when unconfigured
- [ ] 5.2 backend: Proof — golden passes with fixtures/fakes (no live Overpass/OSRM/LLM required)

## 6. FE Revise plan + guidebook/map refresh

- [ ] 6.1 frontend: After draft exists, show **Revise plan** control that POSTs composer text to `/revise` SSE; progress + abort; on `done` refresh session + guidebook export + map stops; chat Send / HITL / catalog / Build plan MUST NOT start revise; cap-hit/error keep previous draft visible
- [ ] 6.2 frontend: Proof — Playwright `frontend/e2e/revise-plan.spec.ts` (fixture or stubbed draft): Revise plan visible; ordinary send does not revise; successful revise updates guidebook/map days/stops (or equivalent testids)

## 7. Local terminal + Playwright MCP + CI

- [ ] 7.1 backend: Local terminal smoke — Compose API/db up; session with draft + catalog fixtures; httpx/curl `POST .../revise` SSE through done; abort mid-run keeps last valid; `GET` session/trip/export structure matches
- [ ] 7.2 frontend: Apply-time Playwright MCP (or browser tools) against local frontend: draft visible → type “less walking day 2” → Revise plan → observe progress → structured itinerary + map stops update; if catalog is thin, seed/fix until the happy path works — do not ship a decorative-only CTA
- [ ] 7.3 infra: Ensure CI (or documented script) runs P6 unit/ASGI/golden + frontend Playwright revise smoke; failures block merge
- [ ] 7.4 docs: Align `system-docs/phase-slices/p6-revision/` validation checkboxes with proofs; if blueprint and `llm.md` §7.5 disagree, resolve both (no third shape); mark blueprint status implemented via this change
