## Purpose

Defines catalog acquire and retrieve for a confirmed trip scope: PostGIS place persistence, region/hub ingest via free places providers, bounded background acquire with honest readiness, and in-scope bbox/category/tags retrieve without inventing venues or foreign fill.

## ADDED Requirements

### Requirement: Places persist with geometry and country identity

The system MUST persist acquired places with stable identity, geometry suitable for spatial query, category/tags metadata, and a country code (or equivalent country identity) used for filtering. Spatial retrieve MUST use an indexed geometry query (GiST or equivalent), not an unbounded full-table scan. The system MUST NOT invent coordinates for places that providers did not supply.

#### Scenario: Upsert then bbox retrieve

- **WHEN** places for a region or hub scope are upserted and a retrieve runs for that scope’s bounding box
- **THEN** matching place identities are returned from persistence and foreign-country identities are not mixed into the result solely because they sit near the border

#### Scenario: Unknown-country places are excluded

- **WHEN** a provider returns a place without a resolvable country matching the trip scope country
- **THEN** that place is not kept as an in-scope catalog result for the trip

### Requirement: Acquire uses region or hub polygons only

After a session has a confirmed `trip_scope`, catalog acquire MUST fetch places for that scope’s region and/or hubs only. Acquire MUST NOT scrape a country-centroid radius, MUST NOT refill with foreign-country POIs when the catalog is thin, and MUST NOT start from chat or HITL resume alone.

#### Scenario: Region scope acquire

- **WHEN** a session with a region (or city) `trip_scope` starts catalog acquire
- **THEN** places providers are queried for that grounded region/hub geography and results are upserted under country filter

#### Scenario: Country scope without hubs is refused or HITL

- **WHEN** a session’s `trip_scope` is country-scale without usable hubs for acquire
- **THEN** acquire does not silently centroid-scrape the country; it refuses, returns a failed/honest status, or requires prior hub resolution/HITL

#### Scenario: Thin catalog stays honest

- **WHEN** providers return few or no places inside the scope
- **THEN** readiness is empty, partial, or failed as appropriate and the system does not invent venues or import foreign POIs to look fuller

### Requirement: Places providers fail soft behind a single facade

External places sources (such as Overpass and OpenTripMap-class APIs) MUST be accessed through one product facade/port. Adapter timeouts, HTTP errors, or empty provider payloads MUST map to typed empty or partial results. The system MUST NOT crash interactive planning solely because a places provider is down, and MUST NOT invent POIs to compensate.

#### Scenario: Provider down yields empty or partial

- **WHEN** a places provider times out or errors during acquire
- **THEN** the acquire path records empty or partial progress with honest readiness and does not fabricate places

#### Scenario: Facade maps provider payloads to places

- **WHEN** a places provider returns valid in-scope features
- **THEN** those features are mapped into persisted place records with real coordinates and metadata (no invented geometry)

### Requirement: Bounded background acquire with user-visible status

Catalog acquire MUST run as a bounded background job after enqueue. Success MUST update session catalog readiness to a ready or partial outcome with place counts when available. Exhausted retries or worker/queue unavailability MUST mark the job failed with user-visible status. Acquire MUST NOT hang indefinitely without status. Interactive API liveness MUST still succeed when Redis/worker are down; acquire enqueue or job completion MUST fail honestly in that case.

#### Scenario: Acquire job succeeds

- **WHEN** acquire is enqueued for a session with a valid region/hub scope and the worker completes ingest
- **THEN** catalog readiness for that session reports ready or partial with a non-negative place count and does not claim success with invented places

#### Scenario: Acquire job fails after bounds

- **WHEN** the acquire job fails after its retry bound or cannot run because the queue/worker is unavailable
- **THEN** catalog readiness reports failed (or equivalent honest status) and the user is not left in an unbounded wait without status

#### Scenario: Idempotent re-enqueue

- **WHEN** acquire is requested again for a session that already has a successful or in-flight acquire
- **THEN** the system does not corrupt place data via unbounded duplicate success paths; re-enqueue is safe (reuse job, no-op, or bounded refresh with clear status)

### Requirement: Retrieve returns real place ids or honest empty

In-scope retrieve MUST filter by the trip scope’s geography (bbox/hubs) and optional category/tags preferences, apply the country filter, and return real persisted place identities. When no matches exist, retrieve MUST return a typed empty result. Empty retrieve MUST NOT invent POIs. HITL for emptiness MAY be deferred to generate; P3 MUST remain honest at the retrieve boundary. v1 retrieve MUST be PostGIS spatial filter (vector index is later).

#### Scenario: Retrieve returns catalog ids

- **WHEN** places exist inside the session scope after acquire and retrieve is called with that scope
- **THEN** the result contains those place identities (and coordinates from persistence) subject to category/tags filters

#### Scenario: Retrieve empty is honest

- **WHEN** no places match the scope and filters
- **THEN** the result is an honest empty retrieve outcome and no fabricated venues are returned

#### Scenario: Foreign country excluded on retrieve

- **WHEN** foreign-country places exist near the scope border in persistence
- **THEN** retrieve for the trip’s resolved country does not include those foreign places

### Requirement: Catalog HTTP exposes readiness and acquire enqueue

The product API MUST expose `GET /api/v1/sessions/{id}/catalog` for owning guests to read catalog readiness/status (and place count when known), and `POST /api/v1/catalog/acquire` with a session id to enqueue acquire. Routes MUST enforce session ownership. The API MUST NOT use Wandr paths. These routes MUST NOT start generate or persist an itinerary.

#### Scenario: Readiness for owner

- **WHEN** the owning guest calls `GET /api/v1/sessions/{id}/catalog` after acquire has completed or failed
- **THEN** the response includes an honest readiness/status payload for that session

#### Scenario: Enqueue acquire

- **WHEN** the owning guest calls `POST /api/v1/catalog/acquire` for a session with confirmed trip_scope suitable for acquire
- **THEN** the API returns a job id and/or status indicating enqueue (or honest failure if the queue is down) without starting generate

#### Scenario: Foreign session catalog denied

- **WHEN** a guest requests catalog readiness or acquire for a session owned by another principal
- **THEN** the API denies the operation and does not leak catalog status or places

### Requirement: Retrieve is observed fail-soft

Retrieve MUST be wrapped in an observability span that records query/filter context and whether the result was empty, when an observability backend is configured. When observability is unconfigured or down, retrieve MUST still complete and MUST NOT crash solely due to missing tracer configuration.

#### Scenario: Retrieve span recorded or no-op

- **WHEN** retrieve runs with observability configured
- **THEN** a retrieve span (or equivalent) is recorded including empty-or-not signal

#### Scenario: Obs down does not block retrieve

- **WHEN** retrieve runs without a configured observability backend
- **THEN** retrieve still returns real ids or honest empty and does not raise solely due to missing tracer configuration
