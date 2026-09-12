# adaptive-country-scope Specification

## Purpose

Defines how the conversational trip OS resolves one city, region, or country and decomposes country-scale prompts by day budget, with HITL when the choice is material. Catalogs and scheduled stops MUST stay inside the resolved country.

## Requirements

### Requirement: One resolved scope per trip

Each planning session MUST resolve to exactly one trip scope kind: city, region, or country. The language model MUST NOT be the sole source of truth for coordinates or admin identity; geo tools (gazetteer/geocoder class) MUST confirm candidates. Ambiguous results MUST HITL rather than silently centroid-plan a country.

#### Scenario: City-scale prompt

- **WHEN** the user asks for a city-scale place that geo tools confirm as city-scale
- **THEN** the trip scope is that city (single planning base) without forcing a country-wide hub list

#### Scenario: Region-scale prompt

- **WHEN** the user asks for a named region (for example Tuscany) that geo tools treat as larger than a city disk
- **THEN** the trip scope is that region, not an arbitrary country centroid

#### Scenario: Country-scale prompt

- **WHEN** the user names a country as the destination
- **THEN** the trip scope kind is country and planning follows day-budget decomposition below — not a single country-centroid radius scrape as the itinerary

### Requirement: Short country stays collapse to the best region

When the resolved scope is a country and the user’s total schedule is short (default: 3 days or fewer, unless the user named a specific city/region), the system MUST keep the itinerary inside **one best region** of that country rather than hopping nationwide. “Best” MUST be computed from grounded signals (catalog quality, travel compactness, preference fit), not from unconstrained model geography.

#### Scenario: Three days in a large country

- **WHEN** the user asks for a 3-day trip in a country and did not name a city or region
- **THEN** the saved itinerary stays within a single selected region of that country and the chat states which region was chosen and why at a high level

#### Scenario: User named a city inside a country stay

- **WHEN** the user asks for 3 days but already named a city
- **THEN** the system uses that city as the scope and does not override it with a different “best region”

### Requirement: Longer country stays select best places that fit the schedule

When the resolved scope is a country and the schedule is longer than the short-stay threshold, the system MUST propose or auto-select a set of **best places/hubs** whose day allocation fits the total days. The system MUST HITL when two hub sets are similarly reasonable or when a long transfer would dominate the trip. Day structure MUST still come from the planning engine, not from free-form city lists in prose.

#### Scenario: Ten days in a country

- **WHEN** the user asks for 10 days in a country without naming cities
- **THEN** the system produces a sequenced hub/place plan that fits ~10 days (or asks HITL between a small number of coherent alternatives) rather than packing the whole country into one compact city loop

#### Scenario: Material hub conflict

- **WHEN** two hub sequences fit the day budget equally poorly or transfers would consume a full day
- **THEN** the system asks the user in chat to pick before saving a nationwide hop itinerary

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

### Requirement: Geo signals first, language model second

Oversized vs city-scale classification MUST prefer deterministic geo metadata (admin level, bbox span, place class) before a language-model hub suggestion. The model MAY fill hub lists when geo metadata is thin, but MUST not bypass HITL when matches are ambiguous.

#### Scenario: Clear city from geocoder

- **WHEN** geo metadata clearly indicates a city-scale result
- **THEN** the system does not spend a hub-suggestion model call as a required step

#### Scenario: Thin metadata country

- **WHEN** the user names a country and hub lists are incomplete from geo tools alone
- **THEN** the system may use a model to suggest candidate regions/hubs, then confirm via tools and HITL as required above
