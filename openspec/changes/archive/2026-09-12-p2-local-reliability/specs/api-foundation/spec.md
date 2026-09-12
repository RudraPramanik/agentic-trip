## ADDED Requirements

### Requirement: Pending schema revisions apply before the API serves product routes

The API process MUST apply pending product schema revisions to the configured database as part of boot, before it accepts `POST /api/v1/sessions` (and other product session routes). A Compose `api` start against a healthy product PostGIS MUST NOT require a separate manual migrate command for those routes to succeed. `GET /health` MUST remain liveness (process up) and MUST NOT be used as proof that schema revisions are applied. `GET /health/ready` MUST remain a database-reachability probe and MUST NOT be treated as a substitute for applying schema.

#### Scenario: Compose API start then create session

- **WHEN** the Compose `api` service starts against a reachable product PostGIS that has not yet received the current session schema
- **THEN** boot applies pending revisions, and a subsequent `POST /api/v1/sessions` can succeed without a separate manual migrate step

#### Scenario: Liveness does not imply schema applied

- **WHEN** the API process is running and the database is reachable but schema application has not yet completed
- **THEN** `GET /health` may still succeed as liveness and MUST NOT be documented or implemented as meaning session tables exist
