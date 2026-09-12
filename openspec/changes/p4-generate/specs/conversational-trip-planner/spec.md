## MODIFIED Requirements

### Requirement: Guest draft is the v1 reopenable trip

Until authenticated save exists, a successful generate MUST persist a session draft the guest can reopen in the same cookie session (ordered days and catalog-grounded stops). That draft MUST be stored with draft status only and MUST NOT count as a saved trip. The system MUST NOT invent an authenticated user or OAuth flow to make the draft durable across devices. Map rendering of those stops MAY ship in a later slice; the draft structure and place identities MUST still be persisted in this generate slice.

#### Scenario: Guest reopens a draft after generate

- **WHEN** generate completes successfully for a guest with no authenticated account
- **THEN** the guest can reopen that session’s itinerary structure (same days and catalog-grounded stops) without signing in

#### Scenario: Draft is not a saved trip

- **WHEN** a guest has only a session draft
- **THEN** the system does not treat that draft as a saved trip for last-trip Explore or later trip-keyed booking

#### Scenario: Draft status is not saved

- **WHEN** generate persists a successful itinerary for a guest
- **THEN** the artifact status is draft and no save API is required for reopen in the same cookie session

### Requirement: Structure from planning engine; narrative from language model

Day structure, stop order, visit windows, and coordinates MUST come from deterministic planning/validation (a travel-engine-class layer), not from unconstrained model prose. Language models MAY write titles, day stories, and preference parsing. A finish/save MUST NOT succeed if validation of the structured itinerary failed, unless the run was explicitly aborted. Abort and wall-clock timeout MUST NOT count as a successful finish or draft save.

#### Scenario: Model prose cannot invent a stop

- **WHEN** the language model names a venue that is not in the retrieved catalog
- **THEN** that venue is not scheduled as a stop with invented coordinates

#### Scenario: Invalid structure is not saved as a success

- **WHEN** validation of day caps, travel, or catalog grounding fails and the run is not aborted
- **THEN** the system does not persist a successful trip artifact from that generate

#### Scenario: Abort is not a successful finish

- **WHEN** generate is aborted or times out before validation success persist
- **THEN** the system does not treat that run as a successful draft save
