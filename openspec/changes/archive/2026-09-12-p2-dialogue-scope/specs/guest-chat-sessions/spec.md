## MODIFIED Requirements

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

## ADDED Requirements

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
