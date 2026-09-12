## MODIFIED Requirements

### Requirement: Named fallback for every external kind

The system MUST map each external dependency kind to a named fallback. Supported kinds MUST include at least: geocoder/gazetteer, catalog acquire, retrieve, LLM, routing, GPS, IP, background worker, observability, and generate timeout. A failure in one kind MUST NOT cascade into invented coordinates, invented venues, or fake polylines.

#### Scenario: Geocoder empty or ambiguous

- **WHEN** geocoding times out, returns empty, or returns multiple plausible matches
- **THEN** the system continues via dialogue HITL or an honest ask and does not silently centroid-plan a country

#### Scenario: Retrieve empty

- **WHEN** place retrieve returns no catalog matches inside the resolved scope
- **THEN** the system reports honest emptiness (v1 retrieve is PostGIS bbox/tags only; a later vector index MAY add geo-fallback when empty/down) and does not schedule invented venues

#### Scenario: Routing geometry missing

- **WHEN** routing cannot supply road geometry for a leg
- **THEN** the map shows stop points (and may use fail-soft travel times) and does not fabricate a polyline

#### Scenario: Generate wall-clock timeout

- **WHEN** a generate run exceeds its wall-clock timeout
- **THEN** remaining generate work stops, no successful trip is persisted from that run, and the outcome is recorded as timeout or aborted — not as a successful plan

#### Scenario: Places provider down during acquire

- **WHEN** Overpass/OTM-class places providers time out or error during catalog acquire
- **THEN** acquire records empty or partial progress with honest readiness and does not invent POIs or scrape a country centroid

#### Scenario: Thin catalog without foreign refill

- **WHEN** acquire yields a thin in-scope catalog
- **THEN** the system keeps honest readiness and does not refill with foreign-country POIs

## ADDED Requirements

### Requirement: Catalog acquire and retrieve stay honest under worker failure

When the catalog acquire background job fails after bounded retries, or Redis/worker is unavailable, the system MUST record a failed or honest readiness outcome visible to the owning guest. Empty retrieve MUST remain an honest empty result. Neither path MUST invent venues, coordinates, or foreign fill.

#### Scenario: Background acquire fails with visible status

- **WHEN** a bounded catalog acquire job fails after retries
- **THEN** session catalog readiness reports failed (or equivalent) and the user is not left in an unbounded wait without status

#### Scenario: Empty retrieve does not invent places

- **WHEN** retrieve finds no in-scope matches after acquire or without prior acquire
- **THEN** the result is typed empty and no fabricated places are returned
