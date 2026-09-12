# fail-soft-boundaries Specification

## Purpose

Defines cross-cutting fail-soft and error-boundary behavior so external failures never become unbounded hangs or hallucinated geography, places, or map geometry.

## Requirements

### Requirement: Named fallback for every external kind

The system MUST map each external dependency kind to a named fallback. Supported kinds MUST include at least: geocoder/gazetteer, catalog acquire, retrieve, LLM, routing, GPS, IP, background worker, observability, and generate timeout. A failure in one kind MUST NOT cascade into invented coordinates, invented venues, or fake polylines. During generate, validation failure, narrative LLM failure, empty retrieve, missing routing times, abort/disconnect, and wall-clock timeout MUST each map to an honest outcome without inventing schedule facts.

#### Scenario: Geocoder empty or ambiguous

- **WHEN** geocoding times out, returns empty, or returns multiple plausible matches
- **THEN** the system continues via dialogue HITL or an honest ask and does not silently centroid-plan a country

#### Scenario: Retrieve empty

- **WHEN** place retrieve returns no catalog matches inside the resolved scope
- **THEN** the system reports honest emptiness (v1 retrieve is PostGIS bbox/tags only; a later vector index MAY add geo-fallback when empty/down) and does not schedule invented venues

#### Scenario: Empty retrieve during generate

- **WHEN** generate retrieve returns no in-scope catalog matches
- **THEN** generate fails honestly (or asks via HITL) and does not invent venues to pack a plan

#### Scenario: Routing geometry missing

- **WHEN** routing cannot supply road geometry for a leg
- **THEN** the map shows stop points (and may use fail-soft travel times) and does not fabricate a polyline

#### Scenario: Routing times missing during pack

- **WHEN** an external routing table is unavailable while packing days
- **THEN** packing uses spherical distance plus penalty for times and does not invent polyline geometry as travel facts

#### Scenario: Generate wall-clock timeout

- **WHEN** a generate run exceeds its wall-clock timeout
- **THEN** remaining generate work stops, no successful trip is persisted from that run, and the outcome is recorded as timeout or aborted — not as a successful plan

#### Scenario: Generate abort or disconnect

- **WHEN** the client disconnects or requests generate abort while generate is running
- **THEN** remaining generate work stops, no successful draft is persisted from that run, and the outcome is aborted or error — not success

#### Scenario: Validation fail blocks success persist

- **WHEN** itinerary validation fails during generate
- **THEN** the system does not persist a successful draft and does not invent replacement venues to force a save

#### Scenario: Narrative LLM fail does not invent stops

- **WHEN** the narrative language-model call fails after structure validation
- **THEN** the system does not invent stop identities; it keeps validated structure without narrative or fails honestly

#### Scenario: Places provider down during acquire

- **WHEN** Overpass/OTM-class places providers time out or error during catalog acquire
- **THEN** acquire records empty or partial progress with honest readiness and does not invent POIs or scrape a country centroid

#### Scenario: Thin catalog without foreign refill

- **WHEN** acquire yields a thin in-scope catalog
- **THEN** the system keeps honest readiness and does not refill with foreign-country POIs

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

### Requirement: Catalog acquire and retrieve stay honest under worker failure

When the catalog acquire background job fails after bounded retries, or Redis/worker is unavailable, the system MUST record a failed or honest readiness outcome visible to the owning guest. Empty retrieve MUST remain an honest empty result. Neither path MUST invent venues, coordinates, or foreign fill.

#### Scenario: Background acquire fails with visible status

- **WHEN** a bounded catalog acquire job fails after retries
- **THEN** session catalog readiness reports failed (or equivalent) and the user is not left in an unbounded wait without status

#### Scenario: Empty retrieve does not invent places

- **WHEN** retrieve finds no in-scope matches after acquire or without prior acquire
- **THEN** the result is typed empty and no fabricated places are returned

### Requirement: PDF and print path fails soft without inventing content

PDF and print rendering MUST treat incomplete GuidebookExport as a hard fail with a clear user-visible error. Render failures MUST leave the stored trip intact. The PDF/print path MUST NOT call the language-model gateway, MUST NOT invent hotels, prices, venues, or coordinates, and MUST NOT fabricate booking rates to fill the document.

#### Scenario: Incomplete export does not invent fill

- **WHEN** GuidebookExport is missing required days/stops for print or PDF
- **THEN** the system fails with a clear error and does not invent hotels, prices, or stops

#### Scenario: Render failure preserves trip

- **WHEN** print or PDF rendering fails after a valid export was loaded
- **THEN** the user sees an error and the trip artifact remains unchanged and reopenable

#### Scenario: No language model on PDF path

- **WHEN** print or PDF rendering runs
- **THEN** the language-model gateway is not called for that path
