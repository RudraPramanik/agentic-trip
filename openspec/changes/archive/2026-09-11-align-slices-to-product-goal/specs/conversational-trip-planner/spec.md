## ADDED Requirements

### Requirement: Guest draft is the v1 reopenable trip

Until authenticated save exists, a successful generate MUST persist a session draft the guest can reopen in the same cookie session (ordered days and catalog-grounded stops). That draft MUST NOT count as a saved trip. The system MUST NOT invent an authenticated user or OAuth flow to make the draft durable across devices.

#### Scenario: Guest reopens a draft after generate

- **WHEN** generate completes successfully for a guest with no authenticated account
- **THEN** the guest can reopen that session’s itinerary (same days and mapped stops) without signing in

#### Scenario: Draft is not a saved trip

- **WHEN** a guest has only a session draft
- **THEN** the system does not treat that draft as a saved trip for last-trip Explore or later trip-keyed booking

### Requirement: Generate starts only from an explicit action

A full itinerary generation MUST start only from an explicit user action after trip scope is confirmed (for example a Build plan control). Sending a dialogue message, receiving HITL chips, or confirming scope MUST NOT by itself start generate.

#### Scenario: Confirming scope does not generate

- **WHEN** the user confirms a trip scope in chat
- **THEN** the system explains the scope and waits for an explicit generate action; it does not acquire catalog or pack days on that turn

#### Scenario: Explicit action starts generate

- **WHEN** trip scope is confirmed and the user takes the explicit generate action
- **THEN** the system starts the expensive generate budget for that session

### Requirement: Generate has a wall-clock timeout

A generate run MUST have a wall-clock timeout. When the timeout fires, the system MUST stop remaining generate work (same as abort), MUST NOT persist a successful trip from that run, and MUST record an honest timeout outcome.

#### Scenario: Generate exceeds the time budget

- **WHEN** a generate run is still in progress when the wall-clock timeout elapses
- **THEN** further generate work stops, no successful trip is persisted from that run, and the client receives an honest timeout or aborted outcome
