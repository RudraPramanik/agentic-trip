# phase-slice-lld Specification

## Purpose

Defines the delivery contract for phase-slice implementation packages: numbered sub-phases at function/class/service/route granularity, SWE/LLD guardrails, and a low-level design document so later code applies stay scoped, consistent, and fail-soft.

## Requirements

### Requirement: Phase slices decompose into numbered sub-phases

Each phase-slice package under `system-docs/phase-slices/` MUST keep its existing folder (`p0-foundation` through `p9-hardening`, including `p5b-pdf-export`) and MUST decompose its work inside `blueprint.md` into numbered sub-phases of the form `P{n}.{m}` (and `P5b.{m}` for the PDF slice). A sub-phase MUST be a small implementation unit (one module concern, one service, one router, one port/adapter, one DTO, or a handful of related functions/classes), not a restatement of the whole phase. Nested sub-phase directories MUST NOT replace the existing slice folders.

#### Scenario: Blueprint lists sub-phases for a foundation slice

- **WHEN** an implementer opens `system-docs/phase-slices/p0-foundation/blueprint.md`
- **THEN** the file contains numbered sub-phases such as `P0.1`, `P0.2`, `P0.3` (and further as needed), each with a distinct scope smaller than the whole P0 phase

#### Scenario: Slice folders stay flat

- **WHEN** the phase-slice catalog is inspected
- **THEN** work remains under existing `pN-*` folders and is not split into nested `p0.1/` package directories

### Requirement: Each sub-phase inventories implementation units and a proof

Every sub-phase section MUST name the modules it may touch and MUST inventory the services, HTTP routes or APIs, DTOs, and classes or functions in scope for that sub-phase (frontend surfaces when the slice owns UI). Every sub-phase MUST declare a proof that can be checked before the next sub-phase starts. A later sub-phase MUST NOT pull work that belongs to a later phase-slice.

#### Scenario: Sub-phase names routes and services

- **WHEN** a sub-phase introduces or extends an HTTP entry
- **THEN** the blueprint names the route (method + path) and the service that owns the use-case, and does not leave the router as the only described unit

#### Scenario: Sub-phase proof gates the next sub-phase

- **WHEN** a sub-phase proof is not satisfied
- **THEN** the slice MUST NOT treat the next sub-phase as started work; phase-level validation still requires all sub-phase proofs in that slice plus the slice exit criteria

### Requirement: Guardrails include SWE, algorithm, and LLD rules

Each slice `guardrails.md`, the shared guardrails files, and the slice template MUST include fail-soft / error-boundary rows **and** a rules list covering software-engineering architecture, efficient algorithm choices for that slice, system-design constraints, and low-level design patterns with consistency rules. Guardrails MUST NOT invent Wandr endpoints, DTOs, or env vars. Product fail-soft kinds in `fail-soft-boundaries` remain in force; this requirement adds delivery/LLD rules alongside them.

#### Scenario: Guardrails are more than fail-soft

- **WHEN** an implementer reads a slice `guardrails.md`
- **THEN** they see a fail-soft table plus explicit SWE/LLD/algorithm/system-design rules applicable to that slice

#### Scenario: Shared rules are reusable

- **WHEN** a new slice is copied from `_template/`
- **THEN** the template points at shared fail-soft and shared SWE/LLD rule sources so authors do not start from an empty rules list

### Requirement: Low-level design document is the LLD SSOT

The repository MUST contain `system-docs/llm.md` as the low-level system design document for this product. That document MUST describe module boundaries, service and port responsibilities, this product’s HTTP API catalog, key sequences, data shapes, and algorithm choices, consistent with `system-docs/architecture-draft.md` (locked decisions L1–L24) and `system-docs/product-goal.md`. It MUST NOT copy or invent Wandr OpenAPI paths. Phase-slice packages MUST reference it. When a blueprint sub-phase and `llm.md` disagree, the conflict MUST be resolved in the same docs change; implementers MUST NOT pick an undocumented third shape.

#### Scenario: LLD document exists and is linked

- **WHEN** an implementer starts any phase-slice
- **THEN** they can open `system-docs/llm.md` and find the module/API/algorithm map for this product, and the slice `references.md` links to that file

#### Scenario: LLD does not import Wandr contracts

- **WHEN** `system-docs/llm.md` lists HTTP routes or DTOs
- **THEN** those contracts belong to this product and are not Wandr `guideagent` paths or invented Wandr fields

### Requirement: Validation tracks sub-phases without weakening phase gates

Each slice `validation.md` MUST list checks per sub-phase (or an equivalent checklist covering every sub-phase proof) in addition to the existing phase-level CI and exit criteria. A phase-slice remains **not done** until every sub-phase proof in that slice and the phase-level validation gate pass. The next phase-slice MUST NOT start until that gate is green.

#### Scenario: Phase gate still blocks the next slice

- **WHEN** some sub-phases in P0 pass but the P0 phase-level validation checklist is incomplete
- **THEN** P1 is not treated as unlocked

#### Scenario: Sub-phase checks are visible

- **WHEN** an implementer opens a slice `validation.md`
- **THEN** they can see which sub-phase proofs are required before the slice is done

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
