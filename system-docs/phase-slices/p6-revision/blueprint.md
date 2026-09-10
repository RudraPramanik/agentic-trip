# P6 Revision — blueprint

> Status: planning blueprint (implement via later OpenSpec `p6-revision`).  
> LLD: [`../../llm.md`](../../llm.md) §7.5

## Goal

In-chat capped replan; structure+map update via engine, not prose-only rewrite.

## Scope / modules

revise_graph, planner, trips

## Step plan

Implement **one sub-phase at a time**.

### P6.1 — Parse revision intent

- **Goal:** Structured patch of prefs / day constraints from chat.
- **Modules:** `src/modules/agents/revise.py`
- **Types:** `RevisionIntent`
- **Functions:** `parse_revision_intent(text, itinerary)`
- **Services:** uses `LlmGateway` role `dialogue`
- **Routes / APIs:** none
- **Algorithms / data:** structured out; unknown venue names ignored
- **Depends on:** P2.1, P4.7
- **Proof:** unit: “less walking day 2” → walk cap patch
- **Non-goals:** unconstrained rewrite of whole trip in prose

### P6.2 — Cap checker

- **Goal:** Enforce loop/day/walk budgets before re-entering generate.
- **Modules:** `src/modules/planner/caps.py`
- **Types:** `ReviseCaps`
- **Functions:** `check_caps(state) -> Ok | StopAndExplain`
- **Services:** planner
- **Routes / APIs:** none
- **Algorithms / data:** bounded revise loops
- **Depends on:** P6.1
- **Proof:** unit: cap hit → stop, keep last valid
- **Non-goals:** raising caps silently

### P6.3 — revise_graph

- **Goal:** Re-enter generate pipeline with caps.
- **Modules:** `src/modules/agents/revise.py`
- **Types:** revise graph
- **Functions:** nodes: parse → caps → retrieve/pack/validate (reuse P4)
- **Services:** same as generate
- **Routes / APIs:** none
- **Algorithms / data:** greedy packer again; not LLM day order
- **Depends on:** P6.2, P4.5
- **Proof:** integration: structure changes; map stops update
- **Non-goals:** new TravelEngine algorithm

### P6.4 — Revise HTTP

- **Goal:** In-chat replan endpoint.
- **Modules:** `src/api/sessions.py` or `revise.py`
- **Types:** request `{ text }`
- **Functions:** `revise_session`
- **Services:** revise use-case / runner
- **Routes / APIs:** `POST /api/v1/sessions/{id}/revise`
- **Algorithms / data:** SSE or result — same abort rules as generate
- **Depends on:** P6.3
- **Proof:** ASGI revise updates itinerary
- **Non-goals:** Wandr paths

### P6.5 — Structure+map update proof

- **Goal:** Golden: less walking day 2 updates structured itinerary within cap.
- **Modules:** `tests/evals/`
- **Types:** fixture
- **Functions:** golden assert
- **Services:** —
- **Routes / APIs:** —
- **Algorithms / data:** —
- **Depends on:** P6.4
- **Proof:** golden passes; validation still required to persist
- **Non-goals:** booking changes

## Proof

Less walking day 2 updates structured itinerary within cap

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
