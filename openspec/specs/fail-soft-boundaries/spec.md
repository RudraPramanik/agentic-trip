# fail-soft-boundaries Specification

## Purpose

Defines cross-cutting fail-soft and error-boundary behavior so external failures never become unbounded hangs or hallucinated geography, places, or map geometry.

## Requirements

### Requirement: Named fallback for every external kind

The system MUST map each external dependency kind to a named fallback. Supported kinds MUST include at least: geocoder/gazetteer, catalog acquire, retrieve, LLM, routing, GPS, IP, background worker, observability, and generate timeout. A failure in one kind MUST NOT cascade into invented coordinates, invented venues, or fake polylines.

#### Scenario: Geocoder empty or ambiguous

- **WHEN** geocoding times out, returns empty, or returns multiple plausible matches
- **THEN** the system continues via dialogue HITL or an honest ask and does not silently centroid-plan a country

#### Scenario: Retrieve empty

- **WHEN** place retrieve returns no catalog matches inside the resolved scope
- **THEN** the system uses an in-scope geo fallback if available, otherwise reports honest emptiness and HITL, and does not schedule invented venues

#### Scenario: Routing geometry missing

- **WHEN** routing cannot supply road geometry for a leg
- **THEN** the map shows stop points (and may use fail-soft travel times) and does not fabricate a polyline

#### Scenario: Generate wall-clock timeout

- **WHEN** a generate run exceeds its wall-clock timeout
- **THEN** remaining generate work stops, no successful trip is persisted from that run, and the outcome is recorded as timeout or aborted — not as a successful plan

### Requirement: Observability and workers fail soft

Observability exporters and background workers MUST NOT take down interactive planning when they fail. Worker failures MUST be marked failed or retried with bounds; observability MUST degrade to no-op when unconfigured or down.

#### Scenario: Tracer unconfigured

- **WHEN** a planning or chat request runs without a configured observability backend
- **THEN** the request still completes its product path and does not crash solely due to missing tracer configuration

#### Scenario: Background job fails

- **WHEN** a bounded background job (such as catalog acquire) fails after retries
- **THEN** the system records a failed/honest readiness outcome and does not leave the user in an unbounded wait without status

### Requirement: No hallucinated schedule facts on LLM failure

When the language model fails to parse, hits a tool-loop cap, or returns unconstrained venue names, the system MUST NOT persist those names as scheduled stops with invented coordinates. Structure and coordinates MUST come from planning/validation over retrieved catalog identities.

#### Scenario: Model names an unknown venue

- **WHEN** the language model names a venue that is not in the retrieved catalog
- **THEN** that venue is not scheduled as a stop with invented coordinates

### Requirement: Required configuration fails fast at boot

The process MUST fail to start with a clear error when required configuration (such as the database URL) is missing. Optional vendor keys MUST NOT be treated as required for boot. The process MUST NOT start in a half-configured state that pretends those required settings exist.

#### Scenario: Missing required database URL

- **WHEN** the process loads settings without a database URL
- **THEN** startup fails with a clear configuration error and the API does not serve traffic

#### Scenario: Missing optional observability keys

- **WHEN** the process loads settings without observability vendor keys
- **THEN** the process still starts and does not treat those keys as required configuration

### Requirement: Unconfigured language-model gateway does not crash import or health

When language-model provider keys are missing, the language-model gateway MUST return a structured unavailable result for a complete call. Importing the gateway MUST NOT raise. Health probes MUST still succeed.

#### Scenario: Complete without keys

- **WHEN** a caller invokes the language-model gateway complete operation with no provider keys configured
- **THEN** the call returns a structured unavailable result and does not raise

#### Scenario: Import without keys

- **WHEN** the language-model gateway module is imported with no provider keys configured
- **THEN** the import succeeds

### Requirement: Unconfigured observability does not block boot or health

When observability vendor keys are missing, the observability port MUST no-op. Importing and calling trace, span, or generation operations MUST NOT raise. Liveness probes MUST still succeed. The process MUST NOT treat observability keys as required configuration.

#### Scenario: Span without keys

- **WHEN** a caller starts a trace or span with no observability vendor keys configured
- **THEN** the call completes as a no-op and does not raise

#### Scenario: Health without observability keys

- **WHEN** the API process is running without observability vendor keys
- **THEN** `GET /health` still returns success

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

### Requirement: Geocoder failures stay honest without silent centroids

When geocoding times out, returns empty, or returns multiple plausible matches during dialogue scope resolution, the system MUST continue via HITL or an honest ask. The system MUST NOT silently centroid-plan a country, invent coordinates, or invent venues to recover.

#### Scenario: Geocoder timeout or empty during dialogue

- **WHEN** dialogue geocode search times out or returns no candidates
- **THEN** the user-facing outcome is HITL or an honest ask, and no trip_scope is persisted from a fabricated country centroid

#### Scenario: Ambiguous geocode waits on candidates

- **WHEN** dialogue geocode search returns multiple plausible matches
- **THEN** the system waits on an in-chat candidate choice and does not silently pick one

### Requirement: Missing trip duration does not persist a trip

When structured intent is missing duration, the system MUST ask in chat and MUST NOT persist trip_scope or an itinerary from that turn.

#### Scenario: Ask without persist

- **WHEN** the user prompt omits duration needed for scope classification
- **THEN** the system asks for clarification and does not write trip_scope from that turn

### Requirement: Dialogue checkpoint store failures stay honest

When the dialogue interrupt/checkpoint store is unavailable, the system MUST return an honest error for that HITL path rather than inventing a completed scope. Interactive planning MUST NOT pretend HITL state was saved when it was not.

#### Scenario: Checkpoint store down

- **WHEN** a dialogue turn needs to interrupt for HITL and the checkpoint store cannot persist interrupt state
- **THEN** the API reports an honest error and does not claim trip_scope was confirmed
