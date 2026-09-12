# api-foundation Specification

## Purpose

Defines the bootable modular-monolith runtime for this product: process liveness, dependency readiness, and importable feature packages that do not require vendor keys or a job queue to start.

## Requirements

### Requirement: Liveness probe is independent of dependencies

The HTTP API MUST expose a liveness probe at `GET /health`. When the process is running, that probe MUST succeed even if the database or optional vendors are down. The probe MUST NOT use Wandr `guideagent` paths.

#### Scenario: Process up with database down

- **WHEN** the API process is running and the database is unreachable
- **THEN** `GET /health` still returns success and does not claim the database is ready

#### Scenario: Process up with no vendor keys

- **WHEN** the API process is running without Langfuse or LLM provider keys
- **THEN** `GET /health` still returns success

### Requirement: Readiness probe reflects the database

The HTTP API MUST expose a readiness probe at `GET /health/ready`. Readiness MUST report whether the database can be reached. The probe MUST NOT report a successful ready state when the database is unreachable. The probe MUST NOT use Wandr `guideagent` paths.

#### Scenario: Database reachable

- **WHEN** the API can ping the configured database
- **THEN** `GET /health/ready` reports a successful ready state that includes a true database indicator

#### Scenario: Database unreachable

- **WHEN** the API cannot ping the configured database
- **THEN** `GET /health/ready` does not report a successful ready state and includes a false database indicator

### Requirement: Runtime boots without optional vendors or Redis

The API process MUST start and serve health probes without Redis, without a background worker, and without LLM or observability vendor keys. Feature packages MUST be importable without performing network I/O or requiring those keys.

#### Scenario: Boot without Redis

- **WHEN** Redis is not running
- **THEN** the API still starts and health probes remain available

#### Scenario: Feature packages import cleanly

- **WHEN** a test imports each feature package with no vendor keys configured
- **THEN** the import completes without network I/O and without raising due to missing optional keys

### Requirement: Product routes are phase-gated after foundation

The HTTP API MUST keep health probes at `GET /health` and `GET /health/ready`. After the chat and dialogue-scope slices ship, the API MAY expose dialogue session routes under `/api/v1/sessions` (create session, send message, get session, resume HITL). After the catalog slice ships, the API MUST expose catalog product routes `GET /api/v1/sessions/{id}/catalog` and `POST /api/v1/catalog/acquire`. After the generate slice ships, the API MUST expose generate product routes `POST /api/v1/sessions/{id}/generate` and `POST /api/v1/sessions/{id}/generate/abort`. After the guidebook-map slice ships, the API MUST expose trip product routes `GET /api/v1/trips/{id}` and `GET /api/v1/trips/{id}/export`. After the PDF-export slice ships, product PDF/print MUST be satisfied by frontend print and client PDF generation from GuidebookExport; the API MUST NOT be required to expose `GET /api/v1/trips/{id}/pdf` in this slice. The API MUST NOT expose trip save, explore, or booking product routes until those slices ship. The API MUST NOT use Wandr `guideagent` paths.

#### Scenario: Session create is a product route

- **WHEN** a client sends `POST /api/v1/sessions`
- **THEN** the API can create a planning session and return a successful session payload with guest cookie semantics

#### Scenario: HITL resume is a product route

- **WHEN** a client sends `POST /api/v1/sessions/{id}/hitl` with a choice for a session that has pending HITL
- **THEN** the API can resume that session’s dialogue HITL and return a session projection (or equivalent success payload) without using Wandr paths

#### Scenario: Catalog readiness is a product route

- **WHEN** a client sends `GET /api/v1/sessions/{id}/catalog` for a session they own
- **THEN** the API returns an honest catalog readiness/status payload without using Wandr paths

#### Scenario: Catalog acquire enqueue is a product route

- **WHEN** a client sends `POST /api/v1/catalog/acquire` with a session id they own and a confirmed trip scope suitable for acquire
- **THEN** the API can enqueue catalog acquire and return a job/status payload without starting generate

#### Scenario: Generate remains non-product until its slice

- **WHEN** a client sends `POST /api/v1/sessions/{id}/generate` for a session they own with confirmed trip_scope after the generate slice ships
- **THEN** the API can start in-process generate and return an SSE stream with progress and a terminal done, error, or aborted outcome without using Wandr paths

#### Scenario: Generate abort is a product route

- **WHEN** a client sends `POST /api/v1/sessions/{id}/generate/abort` for a session they own with generate in progress
- **THEN** the API records abort requested and does not continue unbounded generate spend for that run

#### Scenario: Trip get and export are product routes

- **WHEN** a client sends `GET /api/v1/trips/{id}` or `GET /api/v1/trips/{id}/export` for a trip they own after the guidebook-map slice ships
- **THEN** the API can return the trip artifact or GuidebookExport JSON without using Wandr paths

#### Scenario: PDF print is frontend product without server PDF route

- **WHEN** the PDF-export slice has shipped and a guest prints or downloads a guidebook PDF
- **THEN** the product path uses GuidebookExport from trip export (or equivalent owned export) on the frontend and does not require `GET /api/v1/trips/{id}/pdf`

#### Scenario: Explore and booking remain non-product until their slices

- **WHEN** a client sends explore or booking product routes before those slices ship
- **THEN** the API does not treat those routes as shipped product behavior for this foundation contract

#### Scenario: Trip save and optional server PDF remain non-product until chosen

- **WHEN** a client sends trip-save product routes, or `GET /api/v1/trips/{id}/pdf`, before those capabilities are explicitly shipped
- **THEN** the API does not treat those routes as shipped product behavior for this foundation contract

### Requirement: Acquire needs Redis and worker; API liveness does not

The API process MUST still start and serve `GET /health` without Redis or a background worker. Catalog acquire enqueue and job completion MUST depend on a configured job queue and worker. When Redis or the worker is unavailable, acquire MUST fail with an honest user-visible status rather than hanging, and MUST NOT invent places.

#### Scenario: Health without Redis

- **WHEN** Redis is not running
- **THEN** the API still starts and `GET /health` remains available

#### Scenario: Acquire without worker fails honestly

- **WHEN** a client enqueues catalog acquire and the job queue or worker cannot run the job
- **THEN** catalog readiness becomes failed (or enqueue returns an honest failure) and the client is not left without status

### Requirement: Generate does not require Redis

In-process generate and generate abort MUST run without depending on Redis or a background worker. API liveness MUST remain independent of Redis. Catalog acquire MAY still require Redis/worker as before.

#### Scenario: Generate without Redis

- **WHEN** Redis is not running and an owning guest starts generate for a session with confirmed trip_scope and usable catalog fixtures/fakes
- **THEN** generate can still proceed on the in-process runner path (or fail for non-Redis product reasons) and MUST NOT fail solely because Redis is down

### Requirement: Pending schema revisions apply before the API serves product routes

The API process MUST apply pending product schema revisions to the configured database as part of boot, before it accepts `POST /api/v1/sessions` (and other product session routes). A Compose `api` start against a healthy product PostGIS MUST NOT require a separate manual migrate command for those routes to succeed. `GET /health` MUST remain liveness (process up) and MUST NOT be used as proof that schema revisions are applied. `GET /health/ready` MUST remain a database-reachability probe and MUST NOT be treated as a substitute for applying schema.

#### Scenario: Compose API start then create session

- **WHEN** the Compose `api` service starts against a reachable product PostGIS that has not yet received the current session schema
- **THEN** boot applies pending revisions, and a subsequent `POST /api/v1/sessions` can succeed without a separate manual migrate step

#### Scenario: Liveness does not imply schema applied

- **WHEN** the API process is running and the database is reachable but schema application has not yet completed
- **THEN** `GET /health` may still succeed as liveness and MUST NOT be documented or implemented as meaning session tables exist
