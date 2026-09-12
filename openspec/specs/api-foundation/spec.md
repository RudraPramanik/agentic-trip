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

The HTTP API MUST keep health probes at `GET /health` and `GET /health/ready`. After the chat and dialogue-scope slices ship, the API MAY expose dialogue session routes under `/api/v1/sessions` (create session, send message, get session, resume HITL). The API MUST NOT expose catalog acquire, generate, trip, explore, or booking product routes until those slices ship. The API MUST NOT use Wandr `guideagent` paths.

#### Scenario: Session create is a product route

- **WHEN** a client sends `POST /api/v1/sessions`
- **THEN** the API can create a planning session and return a successful session payload with guest cookie semantics

#### Scenario: HITL resume is a product route

- **WHEN** a client sends `POST /api/v1/sessions/{id}/hitl` with a choice for a session that has pending HITL
- **THEN** the API can resume that session’s dialogue HITL and return a session projection (or equivalent success payload) without using Wandr paths

#### Scenario: Generate remains non-product until its slice

- **WHEN** a client sends `POST /api/v1/sessions/{id}/generate`
- **THEN** the API does not start generate work or return a successful generate stream
