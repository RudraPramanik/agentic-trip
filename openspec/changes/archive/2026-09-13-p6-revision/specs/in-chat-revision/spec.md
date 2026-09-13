## Purpose

Defines capped in-chat replan after a guest draft exists: structured revision intent, a mandatory cap check before another expensive generate, re-entry of the grounded pack-and-validate path, revise SSE, and a structure-plus-map update that is not a prose-only rewrite.

## ADDED Requirements

### Requirement: Revision starts only from the revise product action

A structural replan MUST start only when the owning guest invokes the revise product route (or the Revise plan client control that calls it) after a draft itinerary exists. Dialogue messages, HITL resume, catalog acquire, and Build plan MUST NOT start revise. The system MUST NOT run a full replan on every chat message.

#### Scenario: Revise plan starts replan

- **WHEN** a session has a successful draft and the owning guest submits revision text via Revise plan
- **THEN** the system starts the expensive revise budget for that session and streams revise progress

#### Scenario: Chat send after draft does not revise

- **WHEN** a guest sends an ordinary dialogue message after a draft exists
- **THEN** the system does not start revise and does not replace the draft solely because a message was sent

#### Scenario: No draft cannot revise

- **WHEN** the owning guest calls revise for a session that has no persisted draft itinerary
- **THEN** the system reports an honest failure and does not invent a trip to replan

### Requirement: Revision intent is a structured patch

Revision text MUST be parsed into a structured patch of preferences or day constraints against the current itinerary. Venue names that are not in the retrieved catalog MUST be ignored and MUST NOT be scheduled. The parse MUST NOT treat unconstrained prose as a whole-trip rewrite.

#### Scenario: Less walking becomes a walk-cap patch

- **WHEN** the guest revises with text such as "less walking day 2" on a multi-day draft
- **THEN** the system produces a structured day-2 walk or stop-budget patch and does not rewrite the trip as free-form prose

#### Scenario: Unknown venue name is ignored

- **WHEN** revision text names a venue that is not in the retrieved catalog
- **THEN** that venue is not scheduled as a stop with invented coordinates

### Requirement: Cap checker runs before another generate

Before re-entering the expensive generate pipeline, the system MUST enforce loop, day, and walk budgets. When a cap is hit, the system MUST stop, explain honestly, and keep the last valid itinerary. The system MUST NOT raise those caps silently to force another pack.

#### Scenario: Loop cap keeps last valid

- **WHEN** the session has already used the allowed revise-loop budget
- **THEN** the system stops further replan work, explains the cap, and leaves the last valid draft unchanged

#### Scenario: Caps are not raised silently

- **WHEN** a revision patch would increase walk or day budgets above the session’s established caps
- **THEN** the system refuses that raise, explains, and does not pack under silently enlarged budgets

### Requirement: Replan uses the grounded generate path

A successful revise MUST re-enter retrieve, deterministic day packing over catalog identities, hard validation, optional narrative titles/stories, and draft persist only if validation passed. Day structure and stop order MUST come from the planning engine, not from unconstrained model prose. The revise path MUST NOT invent a new packing algorithm or use the language model to choose stop order.

#### Scenario: Structure changes through the engine

- **WHEN** a valid walk-cap patch is applied and packing/validation succeed
- **THEN** the persisted itinerary days and catalog-only stop identities change via the engine, not by editing narrative text alone

#### Scenario: Validation fail does not persist success

- **WHEN** itinerary validation fails during replan
- **THEN** the system does not persist the invalid itinerary as a successful draft and keeps the last valid plan

### Requirement: Revise streams progress and shares generate abort rules

`POST /api/v1/sessions/{id}/revise` MUST accept `{ "text" }` from the owning guest and MUST stream SSE events of kinds `progress`, `done`, `error`, and `aborted`. Client disconnect, explicit abort of the in-flight expensive run, and wall-clock timeout MUST share the generate abort path: remaining stages stop, the last valid draft is kept, and the stream reports an honest `aborted` or `error` outcome. Revise MUST NOT require Redis. Foreign or unknown sessions MUST be denied without leakage.

#### Scenario: SSE progresses then completes

- **WHEN** an owning guest starts revise for a session that can pack and validate the patch successfully
- **THEN** the client observes one or more `progress` events and a terminal `done` without using Wandr paths

#### Scenario: Abort or timeout keeps last valid

- **WHEN** revise is in progress and the client disconnects, requests abort, or the wall-clock timeout elapses
- **THEN** further replan stages stop, no invalid or partial success is persisted from that run, and the last valid draft remains

#### Scenario: Foreign session cannot revise

- **WHEN** a guest calls revise for a session they do not own
- **THEN** the API denies the request and does not start or mutate another guest’s replan

### Requirement: Successful replan updates structure and map

After a successful revise, the session draft and trip artifact MUST reflect the new validated days and catalog-grounded stops (same trip identity, draft status). Guidebook export and the map MUST show the updated stop points. The system MUST NOT invent coordinates or polylines to draw a prettier line.

#### Scenario: Map stops follow the new structure

- **WHEN** revise completes successfully with a changed day-2 stop set
- **THEN** session draft, trip get/export, and the map stops match that new catalog-grounded structure

#### Scenario: Trip identity stays draft

- **WHEN** revise persists a successful replan
- **THEN** the artifact remains draft status and is not treated as an authenticated saved trip

### Requirement: Less-walking-day-2 golden exists

The eval harness MUST include a golden in which “less walking day 2” (or equivalent) updates the structured itinerary within cap. Validation MUST still be required to persist. Failed or capped revises MUST still leave a trace/eval outcome when observability is configured (or no-op when unconfigured).

#### Scenario: Golden updates structured day 2

- **WHEN** the less-walking-day-2 golden runs against fixtures
- **THEN** day 2’s structured walk or stop budget changes within cap and only catalog identities remain

#### Scenario: Failed or capped revise still traced

- **WHEN** a revise ends in cap-stop, validation failure, abort, or error
- **THEN** observability still records an outcome (or no-ops if unconfigured) and evaluation is not skipped solely because the itinerary was not replaced

### Requirement: Frontend exposes Revise plan after a draft

After a draft itinerary exists, the chat UI MUST show an explicit Revise plan control that sends the composer text to the revise product SSE route. Confirming scope, sending dialogue messages, viewing catalog, or activating Build plan MUST NOT auto-start revise. On successful `done`, the UI MUST refresh the draft, guidebook, and map from the updated structure. Cap-hit and failure outcomes MUST be honest and MUST leave the previous draft visible.

#### Scenario: CTA visible after draft

- **WHEN** the guest session has a draft itinerary and no revise in progress
- **THEN** the UI presents a Revise plan control and does not start revise until the guest activates it with text

#### Scenario: Successful revise refreshes guidebook and map

- **WHEN** Revise plan completes with `done` and a changed structure
- **THEN** the visible draft, guidebook days/stops, and map points update to the new structure
