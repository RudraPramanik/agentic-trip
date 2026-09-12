## MODIFIED Requirements

### Requirement: Longer country stays select best places that fit the schedule

When the resolved scope is a country and the schedule is longer than the short-stay threshold, the system MUST propose or auto-select a set of **best places/hubs** whose day allocation fits the total days. The system MUST HITL when two hub sets are similarly reasonable or when a long transfer would dominate the trip. Day structure MUST still come from the planning engine, not from free-form city lists in prose. When hubs are already confirmed on `trip_scope`, packing MUST sequence days across those hubs rather than collapsing the whole country into one compact city loop.

#### Scenario: Ten days in a country

- **WHEN** the user asks for 10 days in a country without naming cities
- **THEN** the system produces a sequenced hub/place plan that fits ~10 days (or asks HITL between a small number of coherent alternatives) rather than packing the whole country into one compact city loop

#### Scenario: Japan-shaped ten-day golden

- **WHEN** a Japan-shaped ~10-day generate golden runs with country scope and hubs (or HITL requirement)
- **THEN** the resulting plan follows hub sequencing or an honest HITL path rather than a single-city nationwide collapse

#### Scenario: Material hub conflict

- **WHEN** two hub sequences fit the day budget equally poorly or transfers would consume a full day
- **THEN** the system asks the user in chat to pick before saving a nationwide hop itinerary

### Requirement: Country filter on catalog and stops

Places ingested or retrieved for a trip, and stops scheduled on the itinerary, MUST belong to the resolved country of the trip scope. Country filtering MUST apply at catalog upsert and at retrieve, not only at later itinerary validation. Itinerary validation MUST still reject any foreign or unknown-country scheduled stop before draft persist. Border-adjacent catalogs MUST NOT schedule foreign POIs. Unknown-country POIs near a border MUST be excluded rather than guessed into the trip or kept as in-scope catalog matches.

#### Scenario: Border city does not import the neighbor

- **WHEN** a city or region sits near an international border
- **THEN** scheduled stops are in the resolved country only

#### Scenario: Acquire upsert excludes foreign POIs

- **WHEN** a places provider returns features near a border including foreign-country POIs
- **THEN** upsert for that trip’s country keeps only matching-country places (unknown-country excluded)

#### Scenario: Retrieve excludes foreign POIs

- **WHEN** retrieve runs for a trip whose scope country is set
- **THEN** returned place identities are in that country only

#### Scenario: Validate rejects foreign scheduled stop

- **WHEN** packing or any upstream step would schedule a stop outside the resolved country
- **THEN** validation fails and no successful draft is persisted with that foreign stop
