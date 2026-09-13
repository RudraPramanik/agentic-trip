## MODIFIED Requirements

### Requirement: Revision stays in chat after save

The user MUST be able to request changes in chat after a trip exists (drop a stop, change pace, swap a day). In v1 a successful generate draft counts as a trip that can be revised in the same guest session. Revisions that change structure MUST go through the same grounded planning path (not silent rewrite of coordinates in prose). Unbounded revision loops MUST be capped. After a successful replan, the structured itinerary and map MUST update from planning/validation.

#### Scenario: Pace change

- **WHEN** the user says "make day 2 less walking" on a saved trip
- **THEN** the system updates the structured itinerary and map from planning/validation, not by editing only the narrative text

#### Scenario: Guest draft can be revised in chat

- **WHEN** a guest has a successful generate draft and submits "make day 2 less walking" via the in-chat revise action
- **THEN** the system updates the structured itinerary and map from planning/validation within the revise cap, not by editing only the narrative text

#### Scenario: Revision loop cap

- **WHEN** the guest keeps requesting structural revises after the allowed loop budget
- **THEN** the system stops, explains, and keeps the last valid itinerary
