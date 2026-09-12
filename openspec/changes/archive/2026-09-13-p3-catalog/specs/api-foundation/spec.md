## MODIFIED Requirements

### Requirement: Product routes are phase-gated after foundation

The HTTP API MUST keep health probes at `GET /health` and `GET /health/ready`. After the chat and dialogue-scope slices ship, the API MAY expose dialogue session routes under `/api/v1/sessions` (create session, send message, get session, resume HITL). After the catalog slice ships, the API MUST expose catalog product routes `GET /api/v1/sessions/{id}/catalog` and `POST /api/v1/catalog/acquire`. The API MUST NOT expose generate, trip, explore, or booking product routes until those slices ship. The API MUST NOT use Wandr `guideagent` paths.

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

- **WHEN** a client sends `POST /api/v1/sessions/{id}/generate`
- **THEN** the API does not start generate work or return a successful generate stream

## ADDED Requirements

### Requirement: Acquire needs Redis and worker; API liveness does not

The API process MUST still start and serve `GET /health` without Redis or a background worker. Catalog acquire enqueue and job completion MUST depend on a configured job queue and worker. When Redis or the worker is unavailable, acquire MUST fail with an honest user-visible status rather than hanging, and MUST NOT invent places.

#### Scenario: Health without Redis

- **WHEN** Redis is not running
- **THEN** the API still starts and `GET /health` remains available

#### Scenario: Acquire without worker fails honestly

- **WHEN** a client enqueues catalog acquire and the job queue or worker cannot run the job
- **THEN** catalog readiness becomes failed (or enqueue returns an honest failure) and the client is not left without status
