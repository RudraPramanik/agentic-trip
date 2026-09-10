## Why

Existing `system-docs/phase-slices/` packages name whole phases but their step plans are four generic bullets. A later `p0-foundation` (or any `pN`) apply would still be kitchen-sink work: no function/class/route inventory, no sub-phase proofs, and guardrails that only list fail-soft rows. We need numbered sub-phases (P0.1, P0.2, …) inside the **existing** blueprints, plus SWE/LLD rules and a low-level design document, so each later code apply is scoped, consistent, and details-oriented.

## What Changes

- **Work type: docs / cross-cutting planning** (no application feature code in this change’s apply).
- Deepen **every** slice under `system-docs/phase-slices/` **in place** (keep folders `p0-foundation` … `p9-hardening`; do **not** create nested `p0.1/` directories).
- Split each phase into numbered **sub-phases** (`P0.1`, `P0.2`, … / `P5b.1`, …) inside `blueprint.md`, each scoped to a small unit of work: module, service, port, repository, router, DTO, or a handful of functions/classes.
- For each sub-phase, inventory **services / routes / APIs / DTOs / classes / functions** (and FE surfaces where that slice owns UI) with a **sub-phase proof** before the next sub-phase.
- Expand **guardrails** (shared file + `_template` + every slice): fail-soft stays; add SWE architecture, algorithm, system-design, and low-level design pattern rules.
- Add **`system-docs/llm.md`**: low-level system design (LLD) SSOT for humans and coding agents (module/class map, API catalog, sequences, algorithms, consistency rules).
- Align `system-docs/architecture-draft.md` §14–§15, `system-docs/README.md`, and `system-docs/phase-slices/README.md` with the sub-phase + LLD loop.

### Non-goals

- Scaffolding `/src`, Docker, Next.js, or any product runtime in this change (that remains later `p0-foundation` … `p9-hardening`).
- Replacing product SSOT: `system-docs/chat-first-trip-os.md` and main OpenSpec product specs stay authoritative for behavior.
- Inventing Wandr OpenAPI paths, DTOs, or env vars.
- Nested slice folders, microservices split, FE repo split, OAuth, Qdrant, live booking, or OR-Tools in v1.
- Changing fail-soft *kinds* or product requirements for planner / scope / explore / booking.

## Capabilities

### New Capabilities

- `phase-slice-lld`: Delivery contract for implementation packages. Each phase-slice MUST be decomposed into numbered sub-phases at function/class/service/route granularity; each sub-phase MUST name modules, types, APIs, and a proof; guardrails MUST include SWE/LLD/algorithm/system-design rules in addition to fail-soft; `system-docs/llm.md` MUST exist as the LLD SSOT and MUST stay consistent with settled architecture (L1–L24) and the product bible.

### Modified Capabilities

- (none — conversational-trip-planner, adaptive-country-scope, explore-geo-feed, booking-placeholder, and fail-soft-boundaries requirements are unchanged; this change adds a delivery/LLD contract only)

## Impact

- **Docs:** all `system-docs/phase-slices/<id>/{blueprint,guardrails,validation,references}.md`, `_template/`, `SHARED-FAIL-SOFT.md` (or a sibling shared SWE/LLD rules file), `system-docs/llm.md` (new), `system-docs/architecture-draft.md`, `system-docs/README.md`, `system-docs/phase-slices/README.md`.
- **OpenSpec:** new main capability `phase-slice-lld` after archive/sync; per-phase **code** changes remain separate (`p0-foundation`, …).
- **Future code:** implementers apply one sub-phase at a time using blueprint + `llm.md`; no runtime API ships in this apply.
- **Not Wandr:** future HTTP in `llm.md` is this product’s catalog only — never `guideagent` paths.
