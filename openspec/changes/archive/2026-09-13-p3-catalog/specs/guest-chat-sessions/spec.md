## ADDED Requirements

### Requirement: Session projection may surface catalog readiness without starting acquire

After catalog acquire has been enqueued or completed for a session, the owning guest’s session projection MUST be allowed to include catalog readiness/status (for example via the existing session `catalog` field or the dedicated catalog readiness route). Chat turns and HITL resume MUST still NOT start catalog acquire or generate. Confirming `trip_scope` MUST NOT by itself start acquire.

#### Scenario: Catalog status visible after acquire

- **WHEN** acquire has completed or failed for a session the guest owns
- **THEN** the guest can read honest catalog readiness for that session (via catalog route and/or session projection)

#### Scenario: Chat still does not start acquire

- **WHEN** a guest sends a dialogue chat message after trip_scope is confirmed
- **THEN** the turn does not enqueue catalog acquire and does not start generate
