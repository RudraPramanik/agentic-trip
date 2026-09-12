# fail-soft-boundaries Specification

## Purpose

Defines cross-cutting fail-soft and error-boundary behavior so external failures never become unbounded hangs or hallucinated geography, places, or map geometry.

## Requirements

### Requirement: Named fallback for every external kind

The system MUST map each external dependency kind to a named fallback. Supported kinds MUST include at least: geocoder/gazetteer, catalog acquire, retrieve, LLM, routing, GPS, IP, background worker, observability, and generate timeout. A failure in one kind MUST NOT cascade into invented coordinates, invented venues, or fake polylines.

#### Scenario: Geocoder empty or ambiguous

- **WHEN** geocoding times out, returns empty, or returns multiple plausible matches
- **THEN** the system continues via dialogue HITL or an honest ask and does not silently centroid-plan a country

#### Scenario: Retrieve empty

- **WHEN** place retrieve returns no catalog matches inside the resolved scope
- **THEN** the system uses an in-scope geo fallback if available, otherwise reports honest emptiness and HITL, and does not schedule invented venues

#### Scenario: Routing geometry missing

- **WHEN** routing cannot supply road geometry for a leg
- **THEN** the map shows stop points (and may use fail-soft travel times) and does not fabricate a polyline

#### Scenario: Generate wall-clock timeout

- **WHEN** a generate run exceeds its wall-clock timeout
- **THEN** remaining generate work stops, no successful trip is persisted from that run, and the outcome is recorded as timeout or aborted — not as a successful plan

### Requirement: Observability and workers fail soft

Observability exporters and background workers MUST NOT take down interactive planning when they fail. Worker failures MUST be marked failed or retried with bounds; observability MUST degrade to no-op when unconfigured or down.

#### Scenario: Tracer unconfigured

- **WHEN** a planning or chat request runs without a configured observability backend
- **THEN** the request still completes its product path and does not crash solely due to missing tracer configuration

#### Scenario: Background job fails

- **WHEN** a bounded background job (such as catalog acquire) fails after retries
- **THEN** the system records a failed/honest readiness outcome and does not leave the user in an unbounded wait without status

### Requirement: No hallucinated schedule facts on LLM failure

When the language model fails to parse, hits a tool-loop cap, or returns unconstrained venue names, the system MUST NOT persist those names as scheduled stops with invented coordinates. Structure and coordinates MUST come from planning/validation over retrieved catalog identities.

#### Scenario: Model names an unknown venue

- **WHEN** the language model names a venue that is not in the retrieved catalog
- **THEN** that venue is not scheduled as a stop with invented coordinates
