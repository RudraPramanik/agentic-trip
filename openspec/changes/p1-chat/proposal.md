## Why

P0 shipped a bootable modular monolith with health probes, ports, and stub auth/LLM/obs — but guests still cannot create a session or stream a dialogue turn. The next product proof is **guest cookie session + streaming chat** (dialogue budget only). Without P1, later slices (HITL scope, catalog, generate) have no session surface or ownership model to build on.

Work type: **backend + frontend + tests** (cross-cutting within the P1 slice). Not docs-only.

## What Changes

- Implement `CookieAuthAdapter` on `AuthPort` (guest httpOnly cookie `at_guest`; never trust client-supplied `user_id`).
- Persist `TripSessionState` via `SessionRepository` (create/get/save; itinerary nullable).
- Add `ChatService` use-cases: `create_session`, `send_message` (dialogue only), `get_session`.
- Expose product routes under `/api/v1/`:
  - `POST /api/v1/sessions` (+ `Set-Cookie`)
  - `POST /api/v1/sessions/{id}/messages` (SSE: `token` | `message` | `error`)
  - `GET /api/v1/sessions/{id}`
- Cooperative cancel on client disconnect; one obs trace/span per chat turn (no-op if unconfigured).
- Minimal Next.js chat shell that creates a session and streams a reply.
- Automated proofs: unit + ASGI guest round-trip; generate graph not imported/called; fail-soft cases covered.
- Follow `system-docs/phase-slices/p1-chat/` (blueprint P1.1–P1.9, guardrails, validation), `system-docs/llm.md` §5 / §7.1, `SHARED-SWE-LLD.md`, and `SHARED-FAIL-SOFT.md`.

**Non-goals:** OAuth; HITL chips / `POST .../hitl` (P2); `POST .../generate` or `GenerateRunner` (P4); catalog acquire/retrieve (P3); map/guidebook; Wandr `guideagent` paths/DTOs/env; invented coords/POIs/polylines; Build plan CTA (P4.11).

**BREAKING:** none for external clients (P0 had no successful session product routes). **Spec-level:** `api-foundation` no longer forbids session/chat routes once this change ships — generate and later product routes stay forbidden.

## Capabilities

### New Capabilities

- `guest-chat-sessions`: Guest cookie identity, durable trip session, dialogue-only chat service, and `/api/v1` session/message SSE APIs with abort-on-disconnect and fail-soft LLM/obs behavior.

### Modified Capabilities

- `api-foundation`: Lift the P0 ban on session/chat product routes for the dialogue endpoints this slice owns; keep generate, catalog, trip, explore, and booking routes non-product until their slices.
- `fail-soft-boundaries`: Add chat-turn fallbacks — LLM dialogue down → honest SSE `error` with session intact; client disconnect → stop that turn; invalid/foreign session → do not leak another user’s data; obs still no-op.

## Impact

- **Code / APIs:** `src/modules/auth` (cookie adapter), `src/modules/chat` (DTOs, service, repository), `src/api/sessions.py` (or `chat.py`), Alembic migration for sessions, composition-root wiring in `src/main.py`. Routes under `/api/v1/sessions…` only for chat.
- **Frontend:** replace empty `frontend/` with a minimal Next.js chat shell consuming create/send/get.
- **Tests / CI:** unit + ASGI proofs for P1.1–P1.9; CI continues to block on failures; assert generate not invoked on chat-only turns.
- **Docs:** implement against existing `system-docs/phase-slices/p1-chat/`; if blueprint method names and `llm.md` disagree, resolve both in this change (no third shape).
- **Deps:** existing FastAPI/SQLAlchemy stack; FE Next.js + fetch/SSE client. Live LiteLLM optional (stub path must remain honest). No Redis/ARQ required.
