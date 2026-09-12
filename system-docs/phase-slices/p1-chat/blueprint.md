# P1 Chat — blueprint

> Status: planning blueprint (implement via later OpenSpec `p1-chat`).  
> LLD: [`../../llm.md`](../../llm.md) §5, §7.1

## Goal

Guest cookie session + streaming chat round-trip (dialogue budget only; no generate).

## Scope / modules

modules/chat, api chat routes, auth guest cookie, obs chat traces

## Step plan

Implement **one sub-phase at a time**.

### P1.1 — Guest cookie adapter

- **Goal:** Persist guest identity on HTTP cookie via `AuthPort`.
- **Modules:** `src/modules/auth/`
- **Types:** `GuestPrincipal`, `CookieAuthAdapter(AuthPort)`
- **Functions:** `issue_guest()`, `read_principal()`, `set_guest_cookie(response)` (adapter helper; `AuthPort` surface remains `issue_guest` / `read_principal` per `llm.md` §4)
- **Services:** none (port/adapter)
- **Routes / APIs:** none (used by session routes)
- **Algorithms / data:** signed/random guest id; httpOnly cookie
- **Depends on:** P0.6
- **Proof:** unit test issue/read; cookie not readable as another user
- **Non-goals:** OAuth

### P1.2 — Session model + repository

- **Goal:** Persist `TripSessionState` for a guest.
- **Modules:** `src/modules/chat/` (or `trips/` session store)
- **Types:** `TripSessionState`, `SessionRepository`
- **Functions:** `SessionRepository.get`, `save`, `create`
- **Services:** none yet
- **Routes / APIs:** none
- **Algorithms / data:** PK `session_id`; guest `user_id` optional
- **Depends on:** P0.3, P1.1
- **Proof:** round-trip save/load in test DB
- **Non-goals:** itinerary columns required (nullable)

### P1.3 — Chat DTOs + ChatService

- **Goal:** Use-cases for create session and send message (dialogue only).
- **Modules:** `src/modules/chat/service.py`, `src/modules/chat/dto.py`
- **Types:** `CreateSessionResponse`, `SendMessageRequest`, `ChatService`
- **Functions:** `ChatService.create_session`, `send_message`, `get_session`
- **Services:** `ChatService`
- **Routes / APIs:** none (service only)
- **Algorithms / data:** append user message; stub assistant if LLM stub
- **Depends on:** P1.2, P0.7
- **Proof:** unit test with stub LLM and in-memory repo
- **Non-goals:** generate graph; HITL chips

### P1.4 — Create session route

- **Goal:** HTTP create session + Set-Cookie.
- **Modules:** `src/api/sessions.py` (or `chat.py`)
- **Types:** response DTO from P1.3
- **Functions:** `create_session()` router
- **Services:** `ChatService.create_session`
- **Routes / APIs:** `POST /api/v1/sessions`
- **Algorithms / data:** —
- **Depends on:** P1.3
- **Proof:** ASGI test 200 + Set-Cookie
- **Non-goals:** Wandr paths

### P1.5 — Send message SSE

- **Goal:** Stream dialogue reply.
- **Modules:** `src/api/sessions.py`, `ChatService.send_message`
- **Types:** SSE events `token` | `message` | `error`
- **Functions:** `send_message()` router; service streams chunks
- **Services:** `ChatService`
- **Routes / APIs:** `POST /api/v1/sessions/{id}/messages`
- **Algorithms / data:** dialogue budget only
- **Depends on:** P1.4
- **Proof:** ASGI test receives streamed reply for a guest
- **Non-goals:** `POST .../generate`

### P1.6 — Session get + SSE abort

- **Goal:** Projection endpoint; cancel work on disconnect.
- **Modules:** `src/api/sessions.py`, `ChatService.get_session`
- **Types:** session projection DTO
- **Functions:** `get_session()`; disconnect cancel in send stream
- **Services:** `ChatService`
- **Routes / APIs:** `GET /api/v1/sessions/{id}`
- **Algorithms / data:** cooperative cancel
- **Depends on:** P1.5
- **Proof:** GET returns messages; disconnect test stops work
- **Non-goals:** HITL resume route (P2)

### P1.7 — Chat traces

- **Goal:** One trace per chat turn via `ObsPort`.
- **Modules:** `src/modules/monitor/` usage from `ChatService`
- **Types:** —
- **Functions:** `start_trace` / `span` around send
- **Services:** `ChatService` + `ObsPort`
- **Routes / APIs:** none new
- **Algorithms / data:** —
- **Depends on:** P0.8, P1.5
- **Proof:** test with recording obs fake: span recorded **or** no-op without keys
- **Non-goals:** generate spans

### P1.8 — FE chat shell

- **Goal:** Minimal Next.js chat that streams messages.
- **Modules:** `frontend/` chat page + stream client
- **Types:** `ChatShell` component
- **Functions:** `postMessage`, `readSse`
- **Services:** none (client)
- **Routes / APIs:** consumes P1.4–P1.6
- **Algorithms / data:** —
- **Depends on:** P1.5
- **Proof:** documented local: send one message, see streamed text
- **Non-goals:** generate button (P4.11 owns Build plan CTA); map; guidebook

### P1.9 — Proof tests

- **Goal:** Guest round-trip automated.
- **Modules:** `tests/`
- **Types:** —
- **Functions:** pytest ASGI guest message round-trip; no generate invoked
- **Services:** —
- **Routes / APIs:** P1 routes
- **Algorithms / data:** —
- **Depends on:** P1.6, P1.7
- **Proof:** tests green; generate graph not imported/called
- **Non-goals:** scope goldens

## Proof

Send message as guest; receive streamed reply; session persists cookie

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
