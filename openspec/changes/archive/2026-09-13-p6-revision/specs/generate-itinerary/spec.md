## ADDED Requirements

### Requirement: Revise re-enters the generate pipeline

A successful structural replan MUST reuse retrieve, deterministic travel-engine packing over catalog identities, hard validation, optional narrative titles/stories, and draft persist only if validation passed. Revise MUST NOT introduce a second packing algorithm or let the language model choose stop order. Build plan, dialogue messages, HITL, and catalog acquire MUST still not start generate or revise except via their own explicit product actions.

#### Scenario: Replan packs with the same engine rules

- **WHEN** revise applies a valid preference or day-constraint patch and retrieve returns catalog places
- **THEN** days are packed from those catalog identities under the patched caps and persist only after validation succeeds

#### Scenario: Build plan still does not start revise

- **WHEN** the guest activates Build plan after a draft already exists
- **THEN** the system starts generate, not revise, unless the guest separately takes the revise action

### Requirement: Generate abort path covers in-flight revise

An in-flight revise run MUST obey the same cooperative abort, disconnect, and wall-clock timeout rules as generate: remaining stages stop, no successful persist from that run, last valid draft kept, honest aborted or error outcome. Generate abort of the session’s in-flight expensive run MUST stop revise work for that session.

#### Scenario: Abort stops in-flight revise

- **WHEN** revise is in progress and the owning guest requests abort of the in-flight expensive run
- **THEN** further replan stages stop, the last valid draft is kept, and the stream reports aborted or error
