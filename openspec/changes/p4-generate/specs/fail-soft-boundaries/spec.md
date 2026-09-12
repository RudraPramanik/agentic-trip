## MODIFIED Requirements

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
