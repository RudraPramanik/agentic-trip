## ADDED Requirements

### Requirement: Revision and replan fail soft

When a revise loop, day, or walk cap is hit, the system MUST stop and explain and MUST keep the last valid itinerary. When validation fails on replan, the system MUST NOT persist the invalid itinerary as a successful draft. Unknown venues named in revision text MUST NOT be scheduled. Abort, disconnect, and wall-clock timeout during revise MUST share the generate abort path: remaining work stops, last valid is kept, honest aborted or error outcome. None of these cases MUST invent coordinates, venues, or polylines.

#### Scenario: Loop cap hit keeps last valid

- **WHEN** the guest requests another replan after the revise-loop budget is exhausted
- **THEN** the system explains the cap, does not replace the last valid draft, and does not invent a new schedule

#### Scenario: Replan validation fail does not save success

- **WHEN** itinerary validation fails during replan
- **THEN** the system does not persist the invalid plan as success and does not invent replacement venues to force a save

#### Scenario: Unknown venue in revision text is not scheduled

- **WHEN** revision text names a venue that is not in the retrieved catalog
- **THEN** that venue is not scheduled as a stop with invented coordinates

#### Scenario: Revise abort or timeout keeps last valid

- **WHEN** the client disconnects, requests abort, or the wall-clock timeout elapses during revise
- **THEN** remaining replan work stops, the last valid draft remains, and the outcome is aborted or error — not success
