# P2 Dialogue + TripScope + HITL — blueprint

> Status: planning blueprint (implement via later OpenSpec `p2-dialogue-scope`).  
> LLD: [`../../llm.md`](../../llm.md) §7.2, §8

## Goal

Dialogue graph: intent parse, geocode candidates, classify scope, LangGraph interrupt HITL, confirm TripScope.

## Scope / modules

modules/agents/dialogue, modules/geo, chat HITL projection

## Step plan

Implement **one sub-phase at a time**.

### P2.1 — Intent schema + parse

- **Goal:** Structured intent from user text via `LlmGateway` role `dialogue`.
- **Modules:** `src/modules/agents/`, `src/modules/llm/`
- **Types:** `TripIntent` (duration, vibe, constraints)
- **Functions:** `parse_intent(text) -> TripIntent | AskClarification`
- **Services:** called from dialogue graph / ChatService
- **Routes / APIs:** none new
- **Algorithms / data:** JSON schema structured out; missing duration → ask
- **Depends on:** P1.3, P0.7 (live gateway OK)
- **Proof:** unit test: "10 days Japan food slow" fills duration + vibe; missing duration → ask
- **Non-goals:** packing days

### P2.2 — GeoGateway + geocode adapter

- **Goal:** Nominatim-class adapter returning candidates only.
- **Modules:** `src/modules/geo/`
- **Types:** `GeoCandidate`, `NominatimAdapter(GeoGateway)`
- **Functions:** `GeoGateway.search(query) -> list[GeoCandidate]`
- **Services:** none
- **Routes / APIs:** none
- **Algorithms / data:** ranked candidates; timeout → empty list
- **Depends on:** P0.4
- **Proof:** adapter test with httpx mock; empty on timeout
- **Non-goals:** silent pick; country centroid

### P2.3 — geocode_search service

- **Goal:** Service wrapping geo for dialogue; never silent pick.
- **Modules:** `src/modules/geo/service.py`
- **Types:** `GeoSearchResult` (candidates | empty)
- **Functions:** `geocode_search(query)`
- **Services:** `GeoService` (or chat-adjacent)
- **Routes / APIs:** none
- **Algorithms / data:** if 0 or many plausible → HITL path
- **Depends on:** P2.2
- **Proof:** 0/1/N candidates unit tests
- **Non-goals:** acquire catalog

### P2.4 — classify_scope

- **Goal:** Deterministic city/region/country from geo metadata first.
- **Modules:** `src/modules/geo/scope.py` or `agents/`
- **Types:** `TripScope` (`kind`, `geo_id`, `name`, `bbox`, `hubs[]`, `day_budget`)
- **Functions:** `classify_scope(intent, candidate) -> TripScope | NeedsHitl`
- **Services:** used by dialogue graph
- **Routes / APIs:** none
- **Algorithms / data:** admin level + bbox span + place class; LLM hubs only if thin country; named city wins
- **Depends on:** P2.1, P2.3
- **Proof:** unit: Kyoto city; Meghalaya region-ish; Japan 3d → best region flagged for explain
- **Non-goals:** persist itinerary

### P2.5 — dialogue_graph + interrupt

- **Goal:** LangGraph dialogue with HITL interrupt + Postgres checkpointer.
- **Modules:** `src/modules/agents/dialogue.py`
- **Types:** graph state subset of `TripSessionState`
- **Functions:** graph nodes: `parse_intent`, `geocode_search`, `classify_scope`, `request_hitl`, `confirm_scope`
- **Services:** ports/services only inside nodes
- **Routes / APIs:** none (invoked from ChatService)
- **Algorithms / data:** interrupt; not ARQ
- **Depends on:** P2.4, P1.2
- **Proof:** graph test: ambiguous Paris interrupts
- **Non-goals:** generate_graph

### P2.6 — HITL projection + resume API

- **Goal:** FE-readable `hitl` on session; resume by choice.
- **Modules:** `src/api/sessions.py`, `ChatService`
- **Types:** `HitlChoiceRequest`
- **Functions:** `resume_hitl(session_id, choice)`
- **Services:** `ChatService` / session service
- **Routes / APIs:** `POST /api/v1/sessions/{id}/hitl`
- **Algorithms / data:** —
- **Depends on:** P2.5
- **Proof:** ASGI: pending hitl → POST choice → `trip_scope` set
- **Non-goals:** generate

### P2.7 — confirm_scope

- **Goal:** Write `trip_scope` after HITL or unambiguous classify.
- **Modules:** dialogue graph node
- **Types:** `TripScope`
- **Functions:** `confirm_scope(state) -> state`
- **Services:** session repo save
- **Routes / APIs:** none
- **Algorithms / data:** explain chosen scope in chat (LLM copy OK)
- **Depends on:** P2.6
- **Proof:** session has exactly one `trip_scope.kind`
- **Non-goals:** catalog ingest

### P2.8 — FE HITL chips

- **Goal:** In-chat chips for candidates / regions.
- **Modules:** `frontend/` chat HITL UI
- **Types:** `HitlChips`
- **Functions:** POST choice to hitl route
- **Services:** none
- **Routes / APIs:** consumes P2.6
- **Algorithms / data:** —
- **Depends on:** P2.6, P1.8
- **Proof:** documented: pick chip continues same session
- **Non-goals:** search-first page as only path

### P2.9 — Scope goldens

- **Goal:** Offline asserts for scope kinds.
- **Modules:** `tests/evals/`, `src/modules/evals/`
- **Types:** golden fixtures
- **Functions:** eval runner cases
- **Services:** —
- **Routes / APIs:** none
- **Algorithms / data:** —
- **Depends on:** P2.7
- **Proof:** goldens: city/region/country/ambiguous Paris; Meghalaya intent→region-ish; Japan short→best region explained
- **Non-goals:** generate goldens

## Proof

Goldens: city/region/country/ambiguous Paris; Meghalaya intent→region-ish scope; Japan short→best region explained

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
