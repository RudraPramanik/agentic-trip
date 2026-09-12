## MODIFIED Requirements

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
