## MODIFIED Requirements

### Requirement: Last trip location only after a saved trip

The Last trip location tab MUST populate from the geography of a **persisted trip** (the trip’s resolved scope / planning location). The system MUST NOT set this tab from a chat geo-resolve, HITL pick, or unsaved draft. A guest session draft MUST NOT unlock this tab. If the user has no authenticated saved trip, that tab MUST be empty with copy that a saved plan unlocks it. Until authenticated save exists, this tab MUST remain locked for all users.

#### Scenario: No saved trip yet

- **WHEN** a visitor has chatted (even if geo was resolved in conversation) but has not saved a trip
- **THEN** Last trip location is empty / locked and does not show POIs for the chat-resolved place

#### Scenario: After save

- **WHEN** a trip has been saved successfully by an authenticated user
- **THEN** Last trip location can show a place feed for that trip’s location/scope, and Near me remains GPS/IP-based and independent

#### Scenario: Newer saved trip wins

- **WHEN** the user saves a later trip with a different scope
- **THEN** Last trip location follows the most recently saved trip location unless the user explicitly pins another saved trip (pinning is optional; default is latest saved)

#### Scenario: Guest draft does not unlock last-trip

- **WHEN** a guest has a successful generate draft and no authenticated saved trip
- **THEN** Last trip location stays empty / locked
