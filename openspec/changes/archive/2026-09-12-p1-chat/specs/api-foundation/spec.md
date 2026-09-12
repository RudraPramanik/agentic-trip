## REMOVED Requirements

### Requirement: Foundation slice does not expose later-phase product routes

**Reason:** P0 correctly forbade session and other product routes while only health existed. P1 owns guest session and dialogue chat routes, so a blanket ban on `POST /api/v1/sessions` is no longer accurate. Phase gating moves to an explicit allow-list for shipped slices.

**Migration:** Use the ADDED requirement “Product routes are phase-gated after foundation” below. Health probes remain required. Generate, catalog, trip, explore, and booking stay non-product until their slices.

## ADDED Requirements

### Requirement: Product routes are phase-gated after foundation

The HTTP API MUST keep health probes at `GET /health` and `GET /health/ready`. After the chat slice ships, the API MAY expose dialogue session routes under `/api/v1/sessions` (create session, send message, get session). The API MUST NOT expose catalog acquire, generate, trip, explore, or booking product routes until those slices ship. The API MUST NOT use Wandr `guideagent` paths.

#### Scenario: Session create is a product route

- **WHEN** a client sends `POST /api/v1/sessions`
- **THEN** the API can create a planning session and return a successful session payload with guest cookie semantics

#### Scenario: Generate remains non-product until its slice

- **WHEN** a client sends `POST /api/v1/sessions/{id}/generate`
- **THEN** the API does not start generate work or return a successful generate stream
