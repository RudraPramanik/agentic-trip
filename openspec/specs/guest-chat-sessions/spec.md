# guest-chat-sessions Specification

## Purpose

Defines guest cookie identity, durable trip sessions, and dialogue-only chat over `/api/v1` with streaming replies, session projection, and abort-on-disconnect — without starting generate or catalog work.

## Requirements

### Requirement: Guests receive a durable cookie identity

The system MUST identify anonymous visitors with an httpOnly guest cookie issued by the server. Identity MUST come from that cookie (or a newly issued one), never from a client-supplied user id body or query field. The cookie name MUST NOT be a Wandr session cookie name.

#### Scenario: Create session sets guest cookie

- **WHEN** a visitor creates a planning session without an existing guest cookie
- **THEN** the response includes a successful session payload and a `Set-Cookie` for the product guest cookie (httpOnly)

#### Scenario: Client-supplied user id is ignored as identity

- **WHEN** a client sends a message or session request that includes a fabricated `user_id` in the body or query
- **THEN** the system does not treat that value as the authenticated principal and does not grant access to another guest’s session

### Requirement: Guests can create and reopen a planning session

The system MUST allow a guest to create a planning session and later retrieve that session’s projection when they present the matching guest cookie. Sessions MUST persist across requests for that guest. The system MUST NOT require a login wall to start chatting.

#### Scenario: Create session succeeds for a guest

- **WHEN** a guest calls `POST /api/v1/sessions`
- **THEN** the API returns a successful payload that includes a `session_id` and indicates the principal is a guest

#### Scenario: Get session returns messages for the owner

- **WHEN** the owning guest calls `GET /api/v1/sessions/{id}` after prior messages
- **THEN** the API returns a projection that includes the session id and the stored messages

#### Scenario: Foreign session is not leaked

- **WHEN** a guest requests a session that belongs to a different principal
- **THEN** the API does not return that session’s messages or other private projection fields

### Requirement: Dialogue messages stream over SSE without generate

Sending a chat message MUST run on the dialogue budget only and MUST invoke the dialogue scope flow (intent, geo, classify, HITL interrupt when needed) rather than a generate path. The response MUST be an SSE stream that can emit `token`, `message`, `error`, and — when HITL is required — `hitl` events. A chat-only turn MUST NOT start catalog acquire, MUST NOT call generate, and MUST NOT persist an itinerary as a successful plan. The API MUST NOT use Wandr `guideagent` paths.

#### Scenario: Guest message round-trip streams a reply

- **WHEN** a guest with a session sends `POST /api/v1/sessions/{id}/messages` with message text
- **THEN** the client receives an SSE stream that completes with assistant content (via `token` and/or `message` events) and the session remains intact

#### Scenario: Chat turn does not invoke generate

- **WHEN** a guest completes a dialogue message turn
- **THEN** the system does not start generate work and does not expose a successful generate stream for that turn

#### Scenario: Ambiguous place emits hitl on the stream or session

- **WHEN** a guest message requires a place or hub choice because matches are ambiguous
- **THEN** the client can observe pending HITL via an SSE `hitl` event and/or the session projection, and no itinerary is persisted as a successful plan from that turn

### Requirement: Session projection surfaces hitl and trip_scope

`GET /api/v1/sessions/{id}` for the owning guest MUST include pending HITL (when interrupted) and confirmed `trip_scope` (when resolved) in the projection alongside messages. Foreign or unknown sessions MUST still deny without leakage.

#### Scenario: Pending hitl is readable on get

- **WHEN** the owning guest gets a session that is waiting on a HITL choice
- **THEN** the projection includes pending hitl details (kind and candidates or equivalent) the client can render

#### Scenario: Confirmed trip_scope is readable on get

- **WHEN** the owning guest gets a session after scope is confirmed
- **THEN** the projection includes trip_scope with exactly one kind (city, region, or country)

### Requirement: HITL resume continues the same session

The API MUST expose `POST /api/v1/sessions/{id}/hitl` for the owning guest to submit a choice (`choice_id` or clarifying text). A valid resume MUST continue the same session, resolve pending HITL, and write `trip_scope` when classification can complete. Resume MUST NOT start generate or catalog acquire.

#### Scenario: Pending hitl then choice sets trip_scope

- **WHEN** a session has pending HITL and the owning guest posts a valid choice to `POST /api/v1/sessions/{id}/hitl`
- **THEN** the response or subsequent get shows trip_scope set and HITL no longer pending

#### Scenario: Foreign hitl resume is denied

- **WHEN** a guest posts a HITL choice for a session owned by a different principal
- **THEN** the API denies the write and does not leak or mutate that session’s hitl or trip_scope

### Requirement: Client disconnect aborts the in-flight chat turn

When the client disconnects during an in-flight dialogue stream, the server MUST stop remaining work for that turn (cooperative cancel). The session MUST remain usable for a later turn. Disconnect MUST NOT leave unbounded LLM spend for the abandoned turn.

#### Scenario: Disconnect stops dialogue work

- **WHEN** a dialogue SSE stream is in progress and the client disconnects
- **THEN** further work for that turn stops and a later request on the same session can proceed

### Requirement: Chat turns remain observable without requiring a tracer

Each dialogue send MUST attempt one observability trace (or equivalent span boundary) for the turn. When the observability backend is unconfigured or down, the turn MUST still complete its product path without crashing solely due to tracing.

#### Scenario: Trace recorded or no-op

- **WHEN** a guest completes a dialogue send with a recording observability fake configured
- **THEN** a turn-level trace or span is recorded

#### Scenario: Missing tracer does not fail the chat turn

- **WHEN** a guest completes a dialogue send with no observability backend configured
- **THEN** the stream still completes its product outcome and does not crash solely due to missing tracer configuration

### Requirement: Guest session create works after Compose API and database start

When the product API and PostGIS are started via Compose and the API is configured at that database, a guest MUST be able to create a planning session without the operator running a separate manual schema-upgrade command. Identity and cookie rules from existing guest-session requirements still apply. The API MUST NOT use Wandr paths or cookie names.

#### Scenario: Fresh Compose stack then create session

- **WHEN** a guest calls `POST /api/v1/sessions` after Compose `api` and `db` are up and the API has finished boot against that database
- **THEN** the API returns a successful session payload and sets the product guest cookie, without requiring a manual migrate on the host

### Requirement: Session projection may surface catalog readiness without starting acquire

After catalog acquire has been enqueued or completed for a session, the owning guest’s session projection MUST be allowed to include catalog readiness/status (for example via the existing session `catalog` field or the dedicated catalog readiness route). Chat turns and HITL resume MUST still NOT start catalog acquire or generate. Confirming `trip_scope` MUST NOT by itself start acquire.

#### Scenario: Catalog status visible after acquire

- **WHEN** acquire has completed or failed for a session the guest owns
- **THEN** the guest can read honest catalog readiness for that session (via catalog route and/or session projection)

#### Scenario: Chat still does not start acquire

- **WHEN** a guest sends a dialogue chat message after trip_scope is confirmed
- **THEN** the turn does not enqueue catalog acquire and does not start generate

### Requirement: Session projection may surface draft without chat starting generate

After a successful generate for a session, the owning guest’s session projection MUST be allowed to include a draft itinerary summary (for example draft status, day count, and/or stop counts). Chat turns, HITL resume, and confirming `trip_scope` MUST still NOT start generate. Catalog acquire controls MUST still NOT start generate.

#### Scenario: Draft visible after successful generate

- **WHEN** generate has completed successfully for a session the guest owns
- **THEN** the guest can read that a draft exists for the session (via session projection and/or generate done payload) without signing in

#### Scenario: Chat still does not start generate after draft

- **WHEN** a guest sends a dialogue chat message after a draft exists
- **THEN** the turn does not start a new generate run solely because a message was sent

### Requirement: Build plan is the explicit client generate action

The guest chat UI MUST expose an explicit Build plan control after `trip_scope` is confirmed. That control MUST call the generate product route. The UI MUST NOT auto-start generate on scope confirm, HITL choice, catalog readiness change, or ordinary chat send.

#### Scenario: Build plan control after scope

- **WHEN** trip_scope is confirmed for the owning guest
- **THEN** the UI shows Build plan and waits for activation before starting generate SSE

#### Scenario: Catalog panel does not start generate

- **WHEN** the guest views or starts catalog acquire after scope confirm
- **THEN** generate does not start unless Build plan is activated
