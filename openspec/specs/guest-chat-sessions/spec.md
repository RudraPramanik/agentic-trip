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

Sending a chat message MUST run on the dialogue budget only. The response MUST be an SSE stream that can emit `token`, `message`, and `error` events. A chat-only turn MUST NOT start catalog acquire, MUST NOT call generate, and MUST NOT persist an itinerary as a successful plan. The API MUST NOT use Wandr `guideagent` paths.

#### Scenario: Guest message round-trip streams a reply

- **WHEN** a guest with a session sends `POST /api/v1/sessions/{id}/messages` with message text
- **THEN** the client receives an SSE stream that completes with assistant content (via `token` and/or `message` events) and the session remains intact

#### Scenario: Chat turn does not invoke generate

- **WHEN** a guest completes a dialogue message turn
- **THEN** the system does not start generate work and does not expose a successful generate stream for that turn

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
