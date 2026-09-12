## 1. Planner types + travel matrix (P4.2–P4.3)

- [x] 1.1 backend: Add planner domain types (`Itinerary`, `Day`, `Stop`) and `haversine_meters` / `travel_matrix` in `src/modules/planner/` (OSRM optional adapter; else haversine + penalty; never return fake LineString)
- [x] 1.2 backend: Proof — unit: no OSRM → finite times; matrix never invents polyline geometry

## 2. TravelEngine.pack (P4.2)

- [x] 2.1 backend: Implement `TravelEngine.pack` / `pack_days` constrained greedy assign under time/walk/transfer caps; hub sequence when `trip_scope.hubs` present; wire concrete engine in composition root
- [x] 2.2 backend: Proof — unit: all stop ids from input places; respects day_budget length; no LLM stop-order

## 3. validate_itinerary (P4.4)

- [x] 3.1 backend: Implement pure `validate_itinerary(itinerary, catalog_ids, scope) -> ValidateResult` (id ∈ catalog, country filter, day caps, transfer sanity)
- [x] 3.2 backend: Proof — unit: unknown venue fails; foreign POI fails; day-cap fail

## 4. GenerateRunner + timeout (P4.1, P4.8 core)

- [x] 4.1 backend: Implement `InProcessGenerateRunner` (`start` / `abort`) with per-session `abort_requested`, progress emission, and `GENERATE_TIMEOUT_SECONDS` (default 120) sharing the abort path
- [x] 4.2 backend: Proof — unit: start emits progress; abort **or** timeout stops further stages; no success persist after timeout

## 5. TripService.persist_draft (P4.7)

- [x] 5.1 backend: Implement `TripService.persist_draft(session_id, itinerary, validation)` writing session draft (`status=draft` on session itinerary JSONB; add `trips` row only if required for reopen proofs); refuse success persist when validation failed or run aborted
- [x] 5.2 backend: Proof — unit: fail validation → no success persist; success → draft status; last-trip still locked semantics documented/asserted

## 6. Narrative via gateway (P4.6)

- [x] 6.1 backend: Implement `write_narrative` via `LlmGateway` role `narrative` (titles/stories only); post-condition place-id set unchanged; on LLM fail prefer validated structure without narrative or honest fail — never invent stops
- [x] 6.2 backend: Proof — unit: narrative cannot introduce new place ids; LLM fail path does not invent venues

## 7. generate_graph pipeline (P4.5)

- [x] 7.1 backend: Implement generate graph/nodes: retrieve → pack → validate → narrative → persist_draft; check abort between stages; services/ports only (no vendor HTTP/SQL in graph)
- [x] 7.2 backend: Wire runner to graph + CatalogService retrieve + Obs spans/traces (no-op when unconfigured); empty retrieve → honest fail
- [x] 7.3 backend: Proof — integration with fakes: valid catalog → draft; invalid → no persist; failed generate still traced with fake Obs

## 8. Generate HTTP SSE + abort route (P4.8–P4.9)

- [x] 8.1 backend: Add `src/api/generate.py` routes `POST /api/v1/sessions/{id}/generate` (SSE `progress` | `done` | `error` | `aborted`) and `POST /api/v1/sessions/{id}/generate/abort`; ownership checks; disconnect → abort; mount router
- [x] 8.2 backend: Proof — ASGI: progress then done/fail; abort cancels; timeout path; foreign session denied; Redis down does not block generate

## 9. Generate goldens (P4.10)

- [x] 9.1 backend: Add `tests/evals/` generate goldens: Meghalaya/Japan-shaped catalog-only days; Japan-10-days-or-HITL; border/country filter; abandoned generate; failed generate still traced
- [x] 9.2 backend: Proof — goldens pass with fixtures/fakes (no live Overpass/OSRM required)

## 10. FE Build plan CTA (P4.11)

- [x] 10.1 frontend: After `trip_scope` confirmed, show **Build plan** control calling generate SSE; progress UI; optional abort; refresh session draft on `done`; do not auto-start on scope confirm, chat send, or catalog acquire
- [x] 10.2 frontend: Proof — documented/manual: scope confirm waits; CTA starts generate; dialogue message does not

## 11. Local terminal + browser validation + CI

- [x] 11.1 infra: Ensure CI pytest (or documented script) runs P4 unit/ASGI/golden checks; failures block merge
- [x] 11.2 backend: Local terminal smoke — Compose API/db up; seed or fake catalog for a session with trip_scope; curl/httpx `POST .../generate` SSE through done; `POST .../abort` mid-run; assert draft on session GET
- [x] 11.3 frontend: Local browser smoke — guest session → confirm scope → (optional acquire) → Build plan → observe progress → draft visible; abort mid-run shows aborted and no success draft
- [x] 11.4 docs: Align `system-docs/phase-slices/p4-generate/` validation checkboxes with proofs; if blueprint and `llm.md` §7.4/§8 disagree, resolve both (no third shape)
