## ADDED Requirements

### Requirement: Required configuration fails fast at boot

The process MUST fail to start with a clear error when required configuration (such as the database URL) is missing. Optional vendor keys MUST NOT be treated as required for boot. The process MUST NOT start in a half-configured state that pretends those required settings exist.

#### Scenario: Missing required database URL

- **WHEN** the process loads settings without a database URL
- **THEN** startup fails with a clear configuration error and the API does not serve traffic

#### Scenario: Missing optional observability keys

- **WHEN** the process loads settings without observability vendor keys
- **THEN** the process still starts and does not treat those keys as required configuration

### Requirement: Unconfigured language-model gateway does not crash import or health

When language-model provider keys are missing, the language-model gateway MUST return a structured unavailable result for a complete call. Importing the gateway MUST NOT raise. Health probes MUST still succeed.

#### Scenario: Complete without keys

- **WHEN** a caller invokes the language-model gateway complete operation with no provider keys configured
- **THEN** the call returns a structured unavailable result and does not raise

#### Scenario: Import without keys

- **WHEN** the language-model gateway module is imported with no provider keys configured
- **THEN** the import succeeds

### Requirement: Unconfigured observability does not block boot or health

When observability vendor keys are missing, the observability port MUST no-op. Importing and calling trace, span, or generation operations MUST NOT raise. Liveness probes MUST still succeed. The process MUST NOT treat observability keys as required configuration.

#### Scenario: Span without keys

- **WHEN** a caller starts a trace or span with no observability vendor keys configured
- **THEN** the call completes as a no-op and does not raise

#### Scenario: Health without observability keys

- **WHEN** the API process is running without observability vendor keys
- **THEN** `GET /health` still returns success
