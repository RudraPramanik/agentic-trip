## ADDED Requirements

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
