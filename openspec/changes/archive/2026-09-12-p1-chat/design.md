## Context

See `proposal.md` for why. P0 left a bootable FastAPI monolith with `StubAuthAdapter`, `StubLlmGateway`, `NoOpObs`, health/ready, and empty `src/modules/chat`. Implementation follows `system-docs/phase-slices/p1-chat/` (P1.1–P1.9, guardrails, validation), `system-docs/llm.md` §5 / §7.1, `SHARED-SWE-LLD.md`, and `SHARED-FAIL-SOFT.md`.

SWE call chain stays locked: routers → `ChatService` → ports/repositories. P1 owns cookie identity, session persistence, dialogue SSE, abort-on-disconnect, and chat traces. Later slices keep their owners (P2 HITL, P3 catalog, P4 generate/timeout, P9 rate limits).

## Goals / Non-Goals

**Goals:**

- Guest cookie principal that cannot be spoofed via request body.
- Durable `TripSessionState` + dialogue-only `ChatService`.
- `/api/v1/sessions` create / messages (SSE) / get with ownership checks.
- Cooperative cancel on disconnect; obs trace per turn (fail-soft).
- Minimal Next.js chat shell that proves the round-trip locally.
- Automated proofs matching `validation.md` (unit + ASGI + “generate not invoked”).

**Non-Goals:**

- OAuth; HITL route/events as product behavior (P2 may reserve `hitl` SSE name but P1 does not emit it).
- Generate runner, catalog acquire, map, guidebook, Explore, booking.
- Live LiteLLM as a hard requirement (stub/unavailable path must remain honest).
- Wandr paths, DTOs, cookie names, or env vars.
- Invented coordinates, venues, or polylines.

## Decisions

### D1 — Upgrade stub auth to `CookieAuthAdapter` in `modules/auth`

Replace day-to-day use of `StubAuthAdapter` in the composition root with `CookieAuthAdapter` implementing `AuthPort`: `issue_guest(response)`, `read_principal(request)`, cookie write helpers. Cookie name remains **`at_guest`** (httpOnly, SameSite=Lax, Secure when not local). Guest id is a random UUID string (optionally HMAC-signed later if tamper evidence is needed; P1 proof is issue/read + ownership, not cryptographic cookie payload).

**Why not** trust `X-User-Id` or body `user_id`: guardrail — never trust client-supplied identity.  
**Why not** `wandr_session`: product is not Wandr.  
**Alternative:** signed JWT cookie. Deferred — opaque id + server-side session row is enough for P1.

### D2 — Session persistence in Postgres via `SessionRepository`

Store `TripSessionState` keyed by `session_id`, with optional `user_id` / `guest_id` for ownership. Messages as JSON (or JSONB). Columns for itinerary / trip_scope / hitl remain nullable. Alembic migration in this change. Repository methods: `create`, `get`, `save`.

**Why Postgres now:** P0 already requires DB for ready; sessions must survive process restart for the cookie continue proof.  
**Alternative:** in-memory only. Rejected for P1.2 proof (“round-trip save/load in test DB”). Tests may still use a fake repo for pure unit tests of `ChatService`.

### D3 — `ChatService` owns dialogue; routers stay HTTP-thin

`src/modules/chat/service.py` + `dto.py`:

- `create_session` → issue/read guest, persist empty session, return `{ session_id, guest: true }`
- `send_message` → ownership check, append user message, call `LlmGateway` on **dialogue** budget only, stream chunks, append assistant message on success, map LLM unavailable → SSE `error` without destroying session
- `get_session` → ownership check, return projection `{ session_id, messages[], budget, hitl?, trip_scope? }` (nullable fields OK)

Routers in `src/api/sessions.py` parse/serialize only; streaming response built from service async iterator. Composition root wires auth, llm, obs, repository.

**Hard rule:** `send_message` MUST NOT import or call `GenerateRunner`, catalog acquire, or travel engine.

### D4 — SSE event contract (P1 subset)

Events this slice emits: `token`, `message`, `error`. Payload sketches per `llm.md` §5.2. Do not emit `hitl` / `progress` / `done` / `aborted` in P1 product behavior (names reserved for later).

Content-Type: `text/event-stream`. ASGI tests assert at least one streamed reply path for a guest.

### D5 — Disconnect = cooperative cancel

On client disconnect during `POST .../messages`, cancel the in-flight dialogue task / async generator. Prefer `asyncio` cancellation or request `is_disconnected` polling at chunk boundaries. Do not continue LLM calls after cancel. Session row stays; partial assistant text may be omitted or marked incomplete — prefer not persisting a fake complete assistant message after abort.

### D6 — Observability: one trace per turn

`ChatService.send_message` wraps the turn with `ObsPort.start_trace` / `span`. Missing keys → existing `NoOpObs`. Proof: recording fake records a span **or** no-op path does not raise.

### D7 — Frontend: minimal Next.js chat shell

Replace `frontend/.gitkeep` with a small Next.js app (App Router): create session on load, text input, SSE reader, message list. Document local run (API CORS already defaults toward `http://localhost:3000` from P0). No generate button, map, or guidebook.

**Why Next.js now:** blueprint P1.8; architecture stack assumption. Keep UI minimal — proof is stream visibility, not design polish.

### D8 — Testing and CI bar (SWE)

| Layer | Proof |
|-------|--------|
| Unit | Cookie issue/read; session repo save/load; `ChatService` with stub LLM + fake repo |
| ASGI | create + Set-Cookie; SSE stream; GET projection; disconnect cancel; foreign session denied |
| Negative | chat turn does not import/call generate; LLM down → SSE error, session intact; obs no-op |
| FE | documented manual note OK for stream visibility |
| CI | existing pytest job runs new tests; failures block |

Prefer fakes behind ports; no live vendor keys required for green CI.

### D9 — Error / fallback map (slice)

| Kind | Fallback |
|------|----------|
| LLM dialogue down | SSE `error`; session intact |
| Client disconnect | cancel turn work |
| Invalid / foreign session | 404/403-style denial; no leak |
| Obs down / missing | no-op |
| Missing DB | ready already fails; session routes may 503 — do not invent in-memory success in production path |

## Risks / Trade-offs

- **[Risk] SSE + test client flaky disconnect simulation** → Mitigation: use httpx/ASGI streaming APIs; assert cancellation flag or “no further LLM calls after close” via fake gateway counters.
- **[Risk] FE scope creep into generate CTA** → Mitigation: blueprint non-goal; tasks explicitly exclude Build plan button.
- **[Risk] JSON message blob vs normalized tables** → Mitigation: JSONB messages for P1; normalize later if P2 HITL needs queryability.
- **[Trade-off] Opaque guest UUID vs signed cookie** → Opaque id + DB ownership is enough; signing can harden without API change.

## Migration Plan

1. Land Alembic session table + auth/chat modules behind feature routes.
2. Wire routers in `create_app()`; keep health unchanged.
3. Add FE shell; document `compose up` + `npm run dev` path.
4. Expand CI pytest; no Redis/Qdrant required.
5. Rollback: revert deploy; sessions table can remain (harmless) or drop in a follow-up migration if needed.

## Open Questions

None that block specs or tasks. Cookie signing vs opaque UUID is an adapter-internal choice (D1); default opaque UUID unless apply finds an existing signing helper worth reusing.
