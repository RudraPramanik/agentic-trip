## Purpose

Defines abortable itinerary generation for a confirmed trip scope: catalog retrieve, deterministic day packing, hard validation, narrative enrichment, guest draft persist, generate SSE, and an explicit Build plan action.

## ADDED Requirements

### Requirement: Generate starts only from the generate product action

A full itinerary generation MUST start only when the owning guest invokes the generate product route (or the Build plan client control that calls it) after `trip_scope` is confirmed. Dialogue messages, HITL resume, scope confirmation, and catalog acquire MUST NOT start generate.

#### Scenario: Build plan starts generate

- **WHEN** trip scope is confirmed and the owning guest takes the explicit Build plan / generate action
- **THEN** the system starts the expensive generate budget for that session and streams generate progress

#### Scenario: Scope confirm alone does not generate

- **WHEN** the user confirms trip scope without taking Build plan
- **THEN** the system does not start generate and does not persist an itinerary as a successful plan from that confirmation

### Requirement: Generate pipeline is retrieve then pack then validate then narrative then draft

A successful generate run MUST execute this order: retrieve in-scope catalog places, pack days with a deterministic travel engine over those place identities, hard-validate the itinerary, optionally write narrative titles/stories via the language-model gateway narrative role, then persist a session draft only if validation passed. The pipeline MUST NOT call vendor HTTP from the generate graph (services/ports only). The language model MUST NOT choose stop order or invent coordinates.

#### Scenario: Valid catalog yields draft itinerary

- **WHEN** retrieve returns catalog places and packing/validation succeed for a session with confirmed trip_scope
- **THEN** the system persists a structured draft with ordered days and catalog-only stop identities

#### Scenario: Invalid itinerary does not persist success

- **WHEN** validation fails (unknown venue id, foreign country stop, day-cap breach, or transfer insanity)
- **THEN** the system does not persist a successful draft from that run and reports an honest failure outcome

### Requirement: Day packing uses catalog identities only

The travel engine MUST assign stops only from retrieved catalog place identities under the session day budget and time/walk/transfer caps. For region or country-with-hubs scopes, packing MUST respect hub sequence when hubs are present. Packing MUST NOT schedule model-invented venues or foreign-country places.

#### Scenario: All stop ids come from input places

- **WHEN** the engine packs days for a set of retrieved places and a day budget length N
- **THEN** every scheduled stop id is from that input set and the itinerary day count respects the day budget

#### Scenario: Model-named unknown venue is not scheduled

- **WHEN** narrative or other LLM output names a venue absent from the retrieved catalog
- **THEN** that venue is not added as a scheduled stop

### Requirement: Travel times fail soft without invented geometry

Travel-time estimation MUST use a routing table when available; otherwise it MUST use spherical distance plus a penalty. Travel-time helpers MUST NOT return fabricated road polylines or LineString geometry as map facts.

#### Scenario: No routing table still yields finite times

- **WHEN** an external routing table is unavailable during packing
- **THEN** the engine still produces finite travel times via distance-plus-penalty and does not invent polyline geometry

### Requirement: Validation is a hard gate before draft persist

Before persisting a successful draft, the system MUST validate that every stop id is in the retrieved catalog for the run, every stop passes the trip-scope country filter, day caps hold, and transfers are sane. Failed validation MUST block success persist.

#### Scenario: Unknown venue fails validation

- **WHEN** an itinerary contains a stop id not in the retrieved catalog set
- **THEN** validation fails and no successful draft is persisted from that run

#### Scenario: Foreign POI fails validation

- **WHEN** an itinerary contains a stop whose country does not match the resolved trip-scope country
- **THEN** validation fails and that stop is not accepted as a successful schedule fact

### Requirement: Narrative cannot introduce place identities

Narrative enrichment MUST write titles and day stories only through the language-model gateway narrative role. Narrative MUST NOT add, remove, or replace stop place identities. If narrative fails, the system MUST NOT invent stops; it MAY keep a valid structure or fail honestly.

#### Scenario: Narrative preserves stop ids

- **WHEN** narrative runs on a validated itinerary
- **THEN** the set of stop place ids after narrative equals the set before narrative

#### Scenario: Narrative failure does not invent stops

- **WHEN** the narrative language-model call fails after validation passed
- **THEN** the system does not invent new stop identities and either persists the validated structure without narrative or reports an honest failure — never a fabricated venue list

### Requirement: Successful persist is guest draft only

A successful generate MUST persist a session-scoped itinerary with draft status only. The system MUST NOT mark the artifact as a saved trip, MUST NOT expose a save API in this slice, and MUST NOT unlock last-trip Explore from the draft alone.

#### Scenario: Success persists draft status

- **WHEN** generate completes with validation passed
- **THEN** the persisted artifact has draft status and remains reopenable in the same guest cookie session

#### Scenario: Draft does not unlock last-trip

- **WHEN** a guest has only a successful generate draft
- **THEN** the system does not treat that draft as an authenticated saved trip for last-trip Explore

### Requirement: Generate streams progress over SSE and supports abort

`POST /api/v1/sessions/{id}/generate` MUST stream SSE events of kinds `progress`, `done`, `error`, and `aborted` for the owning guest. `POST /api/v1/sessions/{id}/generate/abort` MUST set cooperative abort for that session’s run. Client disconnect, explicit abort, and wall-clock timeout MUST share the abort path: remaining stages stop, no successful draft is persisted from that run, and the stream reports an honest `aborted` or `error` outcome. Generate MUST NOT require Redis.

#### Scenario: SSE progresses then completes

- **WHEN** an owning guest starts generate for a session that can pack and validate successfully
- **THEN** the client observes one or more `progress` events and a terminal `done` (or equivalent success terminal) without using Wandr paths

#### Scenario: Explicit abort stops further work

- **WHEN** generate is in progress and the owning guest calls the generate abort route
- **THEN** further generate stages stop, no successful draft is persisted from that run, and the stream reports aborted or error

#### Scenario: Wall-clock timeout aborts without success persist

- **WHEN** a generate run exceeds its configured wall-clock timeout
- **THEN** remaining work stops via the same abort path, no successful draft is persisted, and the client receives an honest timeout or aborted outcome

#### Scenario: Foreign session cannot generate

- **WHEN** a guest calls generate or abort for a session they do not own
- **THEN** the API denies the request and does not start or abort another guest’s run

### Requirement: Generate goldens and fail traces exist

The eval harness MUST include generate goldens covering Meghalaya-shaped and Japan-shaped catalog-only day structure, Japan ~10-days hub sequence or HITL, border/country filter rejection of foreign stops, abandoned generate, and failed generate that still leaves a trace/eval outcome when observability is configured (or no-op when unconfigured).

#### Scenario: Catalog-only golden days

- **WHEN** Meghalaya-shaped or Japan-shaped generate goldens run against fixtures
- **THEN** produced days contain only catalog stop identities and respect country filter expectations

#### Scenario: Failed generate still traced

- **WHEN** a generate ends in error, abort, or validation failure
- **THEN** observability still records an outcome (or no-ops if unconfigured) and evaluation is not skipped solely because no draft was saved

### Requirement: Frontend exposes Build plan after scope confirm

After `trip_scope` is confirmed, the chat UI MUST show an explicit Build plan control that calls the generate product SSE route. Confirming scope, sending dialogue messages, or viewing catalog readiness MUST NOT auto-start generate.

#### Scenario: CTA visible after scope

- **WHEN** the guest session has a confirmed trip_scope and no generate in progress
- **THEN** the UI presents a Build plan control and does not start generate until the guest activates it

#### Scenario: Dialogue message does not start generate

- **WHEN** the guest sends a chat message after scope confirm without clicking Build plan
- **THEN** generate does not start
