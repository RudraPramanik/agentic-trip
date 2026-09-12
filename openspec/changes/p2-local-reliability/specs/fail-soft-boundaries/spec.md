## ADDED Requirements

### Requirement: Composition-root LLM complete is structured unavailable without keys

When language-model provider keys are missing, the gateway the API process actually wires MUST return a structured unavailable result for complete — not a canned dialogue success string. Dialogue MAY continue via deterministic heuristic intent parse. The process MUST NOT treat a placeholder reply as a successful model complete.

#### Scenario: Unconfigured composition-root complete

- **WHEN** the API process is created with no language-model provider key and a caller invokes complete on the wired gateway
- **THEN** the call returns a structured unavailable result and does not return canned dialogue text as a successful complete

#### Scenario: Missing-duration turn still asks

- **WHEN** a guest sends a place-only prompt such as "Japan food slow" with no provider key configured
- **THEN** the stream asks for duration (or an equivalent honest clarification) and does not persist trip_scope from that turn

### Requirement: Missing product schema fails honestly on session create

When session persistence cannot proceed because the product schema is missing or unapplied, `POST /api/v1/sessions` MUST fail with an honest client-visible error (structured problem payload, not an untyped internal crash that looks like the product is ready). The failure MUST NOT invent a session, cookie-bound trip, or itinerary. `GET /health` MAY still succeed as liveness.

#### Scenario: Create session when session table is missing

- **WHEN** a client calls `POST /api/v1/sessions` and the configured database has no session table
- **THEN** the API does not return a successful session payload and the error is an honest failure rather than an untyped internal crash with no problem body
