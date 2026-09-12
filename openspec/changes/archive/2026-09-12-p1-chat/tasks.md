## 1. Guest cookie adapter (P1.1)

- [x] 1.1 backend: Implement `CookieAuthAdapter` on `AuthPort` (`issue_guest`, `read_principal`, set `at_guest` httpOnly SameSite=Lax); wire it in `create_app` (keep stub only for tests if needed)
- [x] 1.2 backend: Unit test issue/read round-trip; assert client-supplied `user_id` is not used as identity

## 2. Session model + repository (P1.2)

- [x] 2.1 backend: Add `TripSessionState` + Alembic migration (session_id PK, guest ownership, messages JSON/JSONB, nullable itinerary/scope/hitl)
- [x] 2.2 backend: Implement `SessionRepository` (`create`, `get`, `save`) against Postgres
- [x] 2.3 backend: Proof — save/load round-trip in test DB

## 3. Chat DTOs + ChatService (P1.3)

- [x] 3.1 backend: Add `src/modules/chat/dto.py` (`CreateSessionResponse`, `SendMessageRequest`, session projection DTOs)
- [x] 3.2 backend: Implement `ChatService.create_session`, `send_message` (dialogue budget only; no `GenerateRunner`/catalog), `get_session` with ownership checks
- [x] 3.3 backend: Map LLM unavailable/failure to honest stream error without destroying the session
- [x] 3.4 backend: Unit test with stub/fake LLM + in-memory or fake repo; assert generate not imported/called

## 4. Create session route (P1.4)

- [x] 4.1 backend: Add `src/api/sessions.py` router — `POST /api/v1/sessions` calls `ChatService.create_session`; HTTP-only parsing/serialization
- [x] 4.2 backend: Wire router + dependencies in composition root (`CORS` remains usable for local FE)
- [x] 4.3 backend: ASGI proof — 200 + `Set-Cookie` for `at_guest`; payload includes `session_id` and guest indicator

## 5. Send message SSE (P1.5)

- [x] 5.1 backend: `POST /api/v1/sessions/{id}/messages` returns `text/event-stream` with `token` | `message` | `error` events from service iterator
- [x] 5.2 backend: ASGI proof — guest receives streamed reply; foreign/unknown session denied without leakage
- [x] 5.3 backend: ASGI/unit proof — LLM down yields SSE `error` and session remains GET-able

## 6. Session get + SSE abort (P1.6)

- [x] 6.1 backend: `GET /api/v1/sessions/{id}` returns session projection for owner
- [x] 6.2 backend: Cooperative cancel on client disconnect during send stream (no further LLM work after cancel)
- [x] 6.3 backend: Proof — GET returns messages; disconnect test stops work (gateway call counter or cancel flag)

## 7. Chat traces (P1.7)

- [x] 7.1 backend: Wrap `send_message` with `ObsPort` start_trace/span (one per turn)
- [x] 7.2 backend: Proof — recording obs fake records a span; missing keys / `NoOpObs` does not raise or fail the turn

## 8. FE chat shell (P1.8)

- [x] 8.1 frontend: Scaffold minimal Next.js app under `frontend/` (App Router) with chat page + SSE client (`postMessage` / `readSse`)
- [x] 8.2 frontend: On load create session (credentials/cookies); send one message and render streamed text — no generate button, map, or guidebook
- [x] 8.3 docs: Document local run path (API + FE) proving one streamed message

## 9. Slice proof, fail-soft, CI (P1.9)

- [x] 9.1 backend: ASGI guest round-trip test (create → message SSE → get); assert generate not invoked
- [x] 9.2 backend: Cover guardrail fail-soft cases (LLM error, foreign session, obs no-op, disconnect) in automated tests
- [x] 9.3 infra: Ensure CI pytest job runs the new suite (PostGIS service as today; no Redis required); failures block merge
- [x] 9.4 docs: If blueprint method lists and `llm.md` §5 disagree, align both in this change (no third shape)
