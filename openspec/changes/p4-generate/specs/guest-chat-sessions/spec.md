## ADDED Requirements

### Requirement: Session projection may surface draft without chat starting generate

After a successful generate for a session, the owning guest’s session projection MUST be allowed to include a draft itinerary summary (for example draft status, day count, and/or stop counts). Chat turns, HITL resume, and confirming `trip_scope` MUST still NOT start generate. Catalog acquire controls MUST still NOT start generate.

#### Scenario: Draft visible after successful generate

- **WHEN** generate has completed successfully for a session the guest owns
- **THEN** the guest can read that a draft exists for the session (via session projection and/or generate done payload) without signing in

#### Scenario: Chat still does not start generate after draft

- **WHEN** a guest sends a dialogue chat message after a draft exists
- **THEN** the turn does not start a new generate run solely because a message was sent

### Requirement: Build plan is the explicit client generate action

The guest chat UI MUST expose an explicit Build plan control after `trip_scope` is confirmed. That control MUST call the generate product route. The UI MUST NOT auto-start generate on scope confirm, HITL choice, catalog readiness change, or ordinary chat send.

#### Scenario: Build plan control after scope

- **WHEN** trip_scope is confirmed for the owning guest
- **THEN** the UI shows Build plan and waits for activation before starting generate SSE

#### Scenario: Catalog panel does not start generate

- **WHEN** the guest views or starts catalog acquire after scope confirm
- **THEN** generate does not start unless Build plan is activated
