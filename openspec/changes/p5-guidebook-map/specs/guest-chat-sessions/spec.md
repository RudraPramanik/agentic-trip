## MODIFIED Requirements

### Requirement: Session projection may surface draft without chat starting generate

After a successful generate for a session, the owning guest’s session projection MUST be allowed to include a draft itinerary summary (for example draft status, day count, and/or stop counts) and MUST include a stable `trip_id` when a draft trip artifact exists so the client can navigate to trip get/export and guidebook UI. Chat turns, HITL resume, and confirming `trip_scope` MUST still NOT start generate. Catalog acquire controls MUST still NOT start generate.

#### Scenario: Draft visible after successful generate

- **WHEN** generate has completed successfully for a session the guest owns
- **THEN** the guest can read that a draft exists for the session (via session projection and/or generate done payload) without signing in

#### Scenario: Trip id available for guidebook navigation

- **WHEN** generate has completed successfully and a draft trip artifact exists
- **THEN** the session projection and/or generate done payload includes a trip_id usable with trip get/export

#### Scenario: Chat still does not start generate after draft

- **WHEN** a guest sends a dialogue chat message after a draft exists
- **THEN** the turn does not start a new generate run solely because a message was sent
