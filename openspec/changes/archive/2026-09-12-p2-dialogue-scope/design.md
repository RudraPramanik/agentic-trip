## Context

See `proposal.md` for why. P1 left guest cookie sessions, `ChatService` dialogue SSE via `LocalDialogueStub` / `StubLlmGateway`, and nullable `hitl` / `trip_scope` JSONB on the session row — but no dialogue graph, geo adapter, or HITL resume route. `GeoGateway` and `LlmGateway` ports already exist; `modules/geo` and `modules/agents` are empty packages.

Implementation follows `system-docs/phase-slices/p2-dialogue-scope/` (P2.1–P2.9, guardrails, validation), `system-docs/llm.md` §7.2 / §8, `SHARED-SWE-LLD.md`, and `SHARED-FAIL-SOFT.md`. SWE call chain stays locked: routers → `ChatService` → ports/services; graph nodes call services/ports only (no Nominatim HTTP inside the graph module).

## Goals / Non-Goals

**Goals:**

- Live `LiteLlmAdapter` when keys exist; stub/`LlmUnavailable` when missing.
- Structured `TripIntent` parse + ask on missing duration.
- Nominatim-class `GeoGateway` + `geocode_search` (candidates only).
- Deterministic `classify_scope` → one `TripScope` or `NeedsHitl`.
- LangGraph `dialogue_graph` with Postgres checkpointer interrupt/resume.
- Session `hitl` projection, SSE `hitl`, `POST .../hitl`, FE chips.
- Scope goldens + geo fail-soft proofs; CI blocks on failure.

**Non-Goals:**

- Catalog acquire, generate, packing days, map, guidebook, Explore, booking.
- ARQ/Redis for HITL.
- Wandr paths, DTOs, or env vars.
- Silent country centroids; invented coords/POIs/polylines.

## Decisions

### D1 — `LiteLlmAdapter` owns live dialogue complete (P2.1)

Implement `LiteLlmAdapter(LlmGateway)` in `modules/llm`. Composition root: if provider keys present → LiteLLM complete for role `dialogue` (and later narrative/embed reuse); else keep `LocalDialogueStub` or `StubLlmGateway` returning structured unavailable / canned text. Intent parse uses JSON-schema structured output into `TripIntent` (duration, vibe, constraints, place query text). Missing duration → `AskClarification` path — no `trip_scope` write.

**Why not** call vendor SDKs from the graph: architecture L16 — single gateway.  
**Why not** require live keys in CI: fail-soft stub path must stay green.  
**Alternative:** always stub until P4. Rejected — blueprint P2.1 owns live adapter when keys exist.

### D2 — Nominatim-class adapter behind `GeoGateway` (P2.2–P2.3)

`NominatimAdapter` implements `GeoGateway.search(query) -> list[GeoCandidate]` via httpx with timeout. Timeout/error → empty list. `geocode_search` in `modules/geo/service.py` wraps the gateway into `GeoSearchResult` (0 / 1 / N). Never auto-pick when 0 or many plausible. Graph and ChatService depend on the service/port, not httpx.

**Why Nominatim-class:** LLD / blueprint; replaceable adapter later.  
**Alternative:** commercial geocoder now. Deferred — port stays the seam.  
**User-Agent / rate limits:** configure polite Nominatim usage via settings; tests mock httpx.

### D3 — `classify_scope` is pure(ish) code + geo metadata first (P2.4)

Place in `modules/geo/scope.py` (or agents helper imported by geo/service). Inputs: `TripIntent` + selected `GeoCandidate`. Outputs: `TripScope | NeedsHitl`. Rules: admin level + bbox span + place class; named city/region wins; country + short day budget → best-region outcome (flag for explain); country + long budget → populate `hubs[]` or `NeedsHitl`. LLM hub suggestion only when country metadata is thin — still confirm via tools/HITL; never silent centroid.

`TripScope` fields per LLD: `kind`, `geo_id`, `name`, `bbox`, `hubs[]`, `day_budget`.

**Why not** LLM-only classify: adaptive-country-scope + guardrails.  
**Short-stay threshold:** default ≤3 days (product goal / main spec); record in code constants, not magic elsewhere.

### D4 — LangGraph dialogue with Postgres checkpointer (P2.5)

`modules/agents/dialogue.py`: nodes `parse_intent` → `geocode_search` → `classify_scope` → `request_hitl` (interrupt) → `confirm_scope`. State is a subset of `TripSessionState`. Invoke from `ChatService.send_message` after ownership checks. On interrupt: persist `hitl` on session row **and** checkpoint; emit SSE `hitl`. Resume via `ChatService.resume_hitl` → graph update/resume → `confirm_scope`.

HITL is **not** an ARQ job. Prefer Postgres-backed LangGraph saver (same DB as sessions). If checkpointer cannot persist, honest error (D9).

**Why LangGraph interrupt:** architecture L7 + LLD §7.2.  
**Alternative:** ad-hoc “pending_hitl” flag without graph. Rejected — resume/checkpoint semantics belong in the dialogue graph for P4/P6 continuity.  
**Thread id:** bind to `session_id` (one dialogue thread per session).

### D5 — HITL API + session projection (P2.6–P2.7)

- Route: `POST /api/v1/sessions/{id}/hitl` body `{ choice_id }` or `{ text }` → `HitlChoiceRequest`.
- Router stays HTTP-thin; service owns ownership, resume, save.
- `confirm_scope` writes exactly one `trip_scope`, clears/resolves `hitl`, appends explain message (LLM copy OK on dialogue budget; stub OK when keys missing).
- GET projection already has `hitl?` / `trip_scope?` — populate for real.
- SSE events this slice may emit: `token`, `message`, `error`, `hitl`. Still no `progress` / `done` / `aborted`.

### D6 — FE HITL chips (P2.8)

Extend P1 Next.js chat shell: when session/SSE shows pending HITL, render candidate chips; POST choice with credentials; refresh projection / continue messages. No search-first-only gate; no generate button.

### D7 — Scope goldens + eval harness (P2.9)

Add fixtures under `tests/evals/` (and thin runner hooks in `modules/evals` if needed) covering: city Kyoto ~4d; Tuscany-style region; Japan ~3d country-short; “3 days in Kyoto” named-city-wins; Japan 10d hubs-or-HITL; ambiguous Paris; missing duration. Prefer deterministic fakes for geo/LLM in CI; live Nominatim optional offline only.

### D8 — Testing and CI bar (SWE)

| Layer | Proof |
|-------|--------|
| Unit | Intent parse (structured / ask); LiteLLM stub path; Nominatim mock timeout→empty; geocode 0/1/N; classify_scope cases |
| Graph | Ambiguous Paris interrupts |
| ASGI | pending hitl → POST choice → `trip_scope` set; foreign hitl denied |
| Eval | Scope goldens listed above |
| Negative | confirm/HITL does not call generate; no silent centroid |
| FE | documented manual note OK for chip continue |
| CI | pytest job runs new suite; failures block |

### D9 — Error / fallback map (slice)

| Kind | Fallback |
|------|----------|
| Geocoder timeout/empty | HITL or ask; no silent centroid |
| Ambiguous place | Candidates in chat; wait |
| Missing duration | Ask; do not persist trip_scope |
| Checkpoint store down | Honest error; prefer Postgres checkpointer |
| LLM keys missing | Stub / `LlmUnavailable`; no crash |
| Obs down | no-op (unchanged) |

## Risks / Trade-offs

- **[Risk] Nominatim rate limits / flaky live calls** → Mitigation: mock httpx in CI; cache optional later; polite User-Agent + timeout.
- **[Risk] LangGraph checkpointer schema drift vs session JSONB `hitl`** → Mitigation: session `hitl` is the FE SSOT projection; checkpointer holds graph resume state; keep both updated in the same service transaction where practical.
- **[Risk] LocalDialogueStub vs structured intent JSON** → Mitigation: for no-keys path, use a deterministic parse fallback or honest ask rather than inventing hubs; live path uses schema out.
- **[Trade-off] Best-region for country-short without catalog quality signals** → Mitigation: P2 may flag best-region from geo metadata / coarse heuristics and explain; catalog-quality “best” deepens in P3+.
- **[Risk] FE scope creep into generate CTA** → Mitigation: blueprint non-goal; tasks exclude Build plan.

## Migration Plan

1. Land LiteLLM adapter + intent types; keep stub path default in CI.
2. Land geo adapter/service/classify; wire composition root.
3. Land dialogue graph + checkpointer migration/tables as required by LangGraph saver.
4. Wire ChatService send/resume + HITL route; emit SSE `hitl`.
5. FE chips; goldens; expand CI pytest.
6. Rollback: revert deploy; unused geo/checkpointer tables can remain or drop in follow-up.

## Open Questions

None that block specs or tasks. Checkpointer table naming follows whatever the LangGraph Postgres saver expects at apply time; session JSONB remains the product projection.
