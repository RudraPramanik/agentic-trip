## MODIFIED Requirements

### Requirement: Product routes are phase-gated after foundation

The HTTP API MUST keep health probes at `GET /health` and `GET /health/ready`. After the chat and dialogue-scope slices ship, the API MAY expose dialogue session routes under `/api/v1/sessions` (create session, send message, get session, resume HITL). After the catalog slice ships, the API MUST expose catalog product routes `GET /api/v1/sessions/{id}/catalog` and `POST /api/v1/catalog/acquire`. After the generate slice ships, the API MUST expose generate product routes `POST /api/v1/sessions/{id}/generate` and `POST /api/v1/sessions/{id}/generate/abort`. The API MUST NOT expose trip save, explore, or booking product routes until those slices ship. The API MUST NOT use Wandr `guideagent` paths.

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

#### Scenario: Explore and booking remain non-product until their slices

- **WHEN** a client sends explore or booking product routes before those slices ship
- **THEN** the API does not treat those routes as shipped product behavior for this foundation contract

## ADDED Requirements

### Requirement: Generate does not require Redis

In-process generate and generate abort MUST run without depending on Redis or a background worker. API liveness MUST remain independent of Redis. Catalog acquire MAY still require Redis/worker as before.

#### Scenario: Generate without Redis

- **WHEN** Redis is not running and an owning guest starts generate for a session with confirmed trip_scope and usable catalog fixtures/fakes
- **THEN** generate can still proceed on the in-process runner path (or fail for non-Redis product reasons) and MUST NOT fail solely because Redis is down
