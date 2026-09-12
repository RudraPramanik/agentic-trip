## 1. LiteLLM adapter + intent parse (P2.1)

- [x] 1.1 backend: Implement `LiteLlmAdapter` on `LlmGateway` (live complete when keys exist; structured unavailable / stub path when missing); wire composition root without breaking import/health
- [x] 1.2 backend: Add `TripIntent` + ask-clarification types and `parse_intent(text)` (dialogue role, JSON-schema structured out; missing duration → ask, no `trip_scope`)
- [x] 1.3 backend: Proof — unit: "10 days Japan food slow" fills duration + vibe; missing duration → ask; missing keys → stub/unavailable, not crash

## 2. GeoGateway + Nominatim adapter (P2.2)

- [x] 2.1 backend: Add `GeoCandidate` types and `NominatimAdapter(GeoGateway)` with httpx timeout → empty list
- [x] 2.2 backend: Wire geo adapter in composition root via settings (User-Agent / base URL); no Nominatim calls from routers
- [x] 2.3 backend: Proof — adapter test with httpx mock; timeout/error → empty candidates

## 3. geocode_search service (P2.3)

- [x] 3.1 backend: Implement `geocode_search` / `GeoService` wrapping `GeoGateway` → `GeoSearchResult` (0 / 1 / N); never silent pick
- [x] 3.2 backend: Proof — unit tests for 0, 1, and N candidates (N → HITL path signal)

## 4. classify_scope (P2.4)

- [x] 4.1 backend: Implement `classify_scope(intent, candidate) -> TripScope | NeedsHitl` (admin/bbox/place-class first; named city/region wins; country-long → `hubs[]` or HITL; LLM hubs only if thin country)
- [x] 4.2 backend: Proof — unit: Kyoto city; Meghalaya region-ish; Japan 3d best-region flagged; Japan 10d hubs or HITL (not country-without-hubs)

## 5. dialogue_graph + interrupt (P2.5)

- [x] 5.1 backend: Add LangGraph `dialogue_graph` in `modules/agents/dialogue.py` with nodes parse_intent → geocode_search → classify_scope → request_hitl → confirm_scope; ports/services only inside nodes
- [x] 5.2 backend: Postgres checkpointer bound to `session_id`; on interrupt persist session `hitl` projection; HITL is not an ARQ job
- [x] 5.3 backend: Wire `ChatService.send_message` to invoke dialogue graph (dialogue budget only; no generate/catalog)
- [x] 5.4 backend: Proof — graph test: ambiguous Paris interrupts; checkpoint-down → honest error path covered or stubbed

## 6. HITL projection + resume API (P2.6)

- [x] 6.1 backend: Add `HitlChoiceRequest` + `ChatService.resume_hitl`; `POST /api/v1/sessions/{id}/hitl` in sessions router (ownership checks)
- [x] 6.2 backend: Emit SSE `hitl` when interrupt pending; GET session surfaces pending `hitl`
- [x] 6.3 backend: Proof — ASGI: pending hitl → POST choice → session has `trip_scope`; foreign hitl denied

## 7. confirm_scope (P2.7)

- [x] 7.1 backend: Implement `confirm_scope` node/path: write exactly one `trip_scope`, resolve `hitl`, explain chosen scope in chat (stub OK without keys)
- [x] 7.2 backend: Proof — session has exactly one `trip_scope.kind`; confirm does not invoke generate

## 8. FE HITL chips (P2.8)

- [x] 8.1 frontend: Render in-chat HITL chips from pending `hitl` / SSE `hitl`; POST choice to hitl route with credentials
- [x] 8.2 frontend: Continue same session after choice (refresh projection / next message) — no search-first-only path; no generate button
- [x] 8.3 docs: Document manual proof — pick chip continues same session

## 9. Scope goldens, fail-soft, CI (P2.9)

- [x] 9.1 backend: Add scope golden/eval cases: city (Kyoto 4d); Tuscany-style region; country-short (Japan 3d); Kyoto-wins; Japan-10-days-or-HITL; ambiguous Paris; missing duration (ask, no persist)
- [x] 9.2 backend: Cover geo fail-soft (timeout/empty/ambiguous) and missing-duration no-persist in automated tests
- [x] 9.3 infra: Ensure CI pytest (or documented eval script) runs these checks; failures block merge
- [x] 9.4 docs: If blueprint method lists and `llm.md` §7.2/§8 disagree, align both in this change (no third shape)
