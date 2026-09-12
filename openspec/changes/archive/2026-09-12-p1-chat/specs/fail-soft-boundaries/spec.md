## ADDED Requirements

### Requirement: Dialogue LLM failure stays honest and non-destructive

When the language-model gateway is unavailable or fails during a dialogue turn, the system MUST emit an honest SSE `error` (or equivalent stream error outcome) and MUST keep the session intact for retry. The failure MUST NOT invent coordinates, venues, or itinerary structure, and MUST NOT start generate to “recover.”

#### Scenario: LLM dialogue down

- **WHEN** a guest sends a chat message and the language-model gateway returns unavailable or fails for that dialogue call
- **THEN** the stream reports an honest error outcome, the session remains retrievable, and no itinerary is persisted as a successful plan from that turn

### Requirement: Invalid or foreign session access does not leak data

When a session id is missing, malformed, or owned by another principal, the system MUST deny access without returning another user’s messages or projection. The system MAY issue or continue a guest cookie for the caller, but MUST NOT attach the caller to a foreign session.

#### Scenario: Unknown session id

- **WHEN** a guest requests get-session or send-message for a session id that does not exist
- **THEN** the API does not return another user’s data and does not treat the call as a successful foreign-session read

#### Scenario: Session owned by another guest

- **WHEN** a guest presents a valid cookie but targets a session owned by a different principal
- **THEN** the API denies the read or write and does not leak that session’s messages
