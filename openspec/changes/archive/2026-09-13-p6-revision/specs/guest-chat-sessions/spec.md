## ADDED Requirements

### Requirement: Revise plan is the explicit client replan action

After a draft itinerary exists, the guest chat UI MUST expose an explicit Revise plan control that calls the revise product route with composer text. The UI MUST NOT auto-start revise on scope confirm, HITL choice, catalog readiness change, ordinary chat send, or Build plan. Dialogue `POST .../messages` MUST remain dialogue-budget only.

#### Scenario: Revise plan control after draft

- **WHEN** a draft exists for the owning guest
- **THEN** the UI shows Revise plan and waits for activation with revision text before starting revise SSE

#### Scenario: Chat still does not start revise after draft

- **WHEN** a guest sends a dialogue chat message after a draft exists
- **THEN** the turn does not start revise and does not replace the draft solely because a message was sent
