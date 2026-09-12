## Why

P1 shipped guest cookie sessions and dialogue-only SSE chat, but a chat turn still cannot resolve geography into a durable `trip_scope`. Without intent parse, geocode candidates, deterministic scope classification, and in-chat HITL interrupt/resume, later slices (catalog acquire, generate) have no grounded scope to plan against. P1 is done; P2 is the next product proof.

Work type: **backend + frontend + tests** (cross-cutting within the P2 slice). Not docs-only.

## What Changes

- Upgrade `LlmGateway` day-to-day path with `LiteLlmAdapter`: live complete when keys exist; keep P0 stub/`LlmUnavailable` when missing.
- Add structured intent parse (`TripIntent` / ask-clarification) on the dialogue budget.
- Implement `GeoGateway` + Nominatim-class adapter and `geocode_search` (candidates only; never silent pick).
- Add deterministic `classify_scope` → `TripScope | NeedsHitl` (geo metadata first; country-long → `hubs[]` or HITL).
- Wire LangGraph `dialogue_graph` with Postgres checkpointer: parse → geocode → classify → interrupt HITL → confirm scope.
- Project pending `hitl` on the session; emit SSE `hitl`; resume via `POST /api/v1/sessions/{id}/hitl`.
- Persist exactly one `trip_scope` after unambiguous classify or HITL choice; explain scope in chat.
- Add FE in-chat HITL chips that POST the choice and continue the same session.
- Scope goldens / eval cases per `system-docs/phase-slices/p2-dialogue-scope/validation.md`.
- Follow `system-docs/phase-slices/p2-dialogue-scope/` (P2.1–P2.9, guardrails, validation), `system-docs/llm.md` §7.2 / §8, `SHARED-SWE-LLD.md`, and `SHARED-FAIL-SOFT.md`.

**Non-goals:** catalog acquire/retrieve (P3); `POST .../generate` / Build plan CTA (P4); packing days; map/guidebook; Wandr paths/DTOs/env; silent country centroid; invented coords/POIs/polylines; ARQ for HITL.

**BREAKING:** none for external clients beyond additive HITL behavior on existing sessions. **Spec-level:** `api-foundation` / `guest-chat-sessions` gain the HITL resume route and `hitl` SSE event; generate and later product routes stay forbidden.

## Capabilities

### New Capabilities

- `dialogue-hitl-scope`: Structured intent parse, geo search/classify into `TripScope`, LangGraph dialogue interrupt/resume HITL, session `hitl`/`trip_scope` projection, FE chips, and scope golden proofs.

### Modified Capabilities

- `guest-chat-sessions`: Dialogue turns invoke the dialogue graph (not stub-only chat); session projection MUST surface pending `hitl` and confirmed `trip_scope`; SSE MAY emit `hitl`; resume continues the same session without generate.
- `api-foundation`: Allow `POST /api/v1/sessions/{id}/hitl` as a product route; keep catalog/generate/trip/explore/booking non-product until their slices.
- `fail-soft-boundaries`: Add P2 dialogue/geo/checkpoint fallbacks — geocode timeout/empty → HITL or ask (no silent centroid); missing duration → ask, no persist; checkpoint store down → honest error; ambiguous place → wait on candidates.

## Impact

- **Code / APIs:** `src/modules/llm` (`LiteLlmAdapter`), `src/modules/geo` (gateway, Nominatim adapter, `geocode_search`, `classify_scope`), `src/modules/agents/dialogue.py` (graph + interrupt), `ChatService` resume/wiring, `src/api/sessions.py` HITL route, session repo fields for `intent` / `hitl` / `trip_scope`, Postgres LangGraph checkpointer.
- **Frontend:** HITL chips on the P1 chat shell; POST choice to hitl route; no search-first-only path.
- **Tests / CI:** unit + ASGI proofs for P2.1–P2.9; scope goldens; geo fail-soft mocks; CI blocks on failures. Prefer fakes behind ports (no live Nominatim/LLM keys required for green CI).
- **Docs:** implement against existing `system-docs/phase-slices/p2-dialogue-scope/`; if blueprint method names and `llm.md` disagree, resolve both in this change (no third shape).
- **Deps:** LangGraph + Postgres checkpointer; httpx for Nominatim; existing FastAPI/SQLAlchemy/Next.js stack. No Redis/ARQ for HITL.
