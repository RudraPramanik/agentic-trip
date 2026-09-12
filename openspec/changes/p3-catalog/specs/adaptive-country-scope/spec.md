## MODIFIED Requirements

### Requirement: Country filter on catalog and stops

Places ingested or retrieved for a trip, and stops scheduled on the itinerary, MUST belong to the resolved country of the trip scope. Country filtering MUST apply at catalog upsert and at retrieve, not only at later itinerary validation. Border-adjacent catalogs MUST NOT schedule foreign POIs. Unknown-country POIs near a border MUST be excluded rather than guessed into the trip or kept as in-scope catalog matches.

#### Scenario: Border city does not import the neighbor

- **WHEN** a city or region sits near an international border
- **THEN** scheduled stops are in the resolved country only

#### Scenario: Acquire upsert excludes foreign POIs

- **WHEN** a places provider returns features near a border including foreign-country POIs
- **THEN** upsert for that trip’s country keeps only matching-country places (unknown-country excluded)

#### Scenario: Retrieve excludes foreign POIs

- **WHEN** retrieve runs for a trip whose scope country is set
- **THEN** returned place identities are in that country only
