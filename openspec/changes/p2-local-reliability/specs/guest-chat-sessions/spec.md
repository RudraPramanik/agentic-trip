## ADDED Requirements

### Requirement: Guest session create works after Compose API and database start

When the product API and PostGIS are started via Compose and the API is configured at that database, a guest MUST be able to create a planning session without the operator running a separate manual schema-upgrade command. Identity and cookie rules from existing guest-session requirements still apply. The API MUST NOT use Wandr paths or cookie names.

#### Scenario: Fresh Compose stack then create session

- **WHEN** a guest calls `POST /api/v1/sessions` after Compose `api` and `db` are up and the API has finished boot against that database
- **THEN** the API returns a successful session payload and sets the product guest cookie, without requiring a manual migrate on the host
