## ADDED Requirements

### Requirement: Product-goal laws have named owner sub-phases

Phase-slice packages MUST assign a named sub-phase and a checkable proof to each of these product-goal laws: v1 guest draft vs saved trip; explicit generate action; wall-clock generate timeout; country-long hub sequence or HITL; bible eval goldens including failed-generate traces; Explore plan-from-card, tab-anchor independence, and IP approximate copy. The LLD MUST name the same owners. A later slice MAY harden a law only after an earlier slice owns the first implementation. The program MUST NOT add a twelfth product phase for these laws.

#### Scenario: Timeout is owned before hardening

- **WHEN** an implementer reads the P4 and P9 blueprints
- **THEN** P4 names a sub-phase whose proof includes wall-clock generate timeout, and P9 does not introduce timeout as a new product behavior

#### Scenario: Generate action has a P4 owner

- **WHEN** an implementer reads the P1 and P4 blueprints
- **THEN** P1 still forbids starting generate from a dialogue-only shell, and P4 names a sub-phase for the explicit generate action after scope is confirmed

#### Scenario: Bible goldens are listed as proofs

- **WHEN** an implementer reads P2 and P4 validation gates
- **THEN** the listed goldens include city, region, country-short, country-short with named city, country-long or HITL, ambiguous place, border/country filter, missing duration, abandoned generate, and failed generate still traced
