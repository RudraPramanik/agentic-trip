## Context

See `proposal.md` for motivation. Settled product/architecture live in `system-docs/chat-first-trip-os.md` and `system-docs/architecture-draft.md` (L1–L23). This change does **not** scaffold the FastAPI app; it locks delivery docs and fail-soft law so later phase applies stay coherent.

## Goals / Non-Goals

**Goals:**

- Root modular-monolith layout (`/src`, not `/backend`) with service-separated modules.
- Complete `phase-slices/` catalog (P0–P9 + P5b) with blueprint / guardrails / validation / references.
- Fail-soft capability as normative spec; every slice documents its failure table.
- Clear split: this change = program docs; per-phase OpenSpec changes = code.

**Non-Goals:**

- Implementing health endpoints, LangGraph, or frontend in this apply.
- Choosing final LiteLLM model id strings.
- Introducing Qdrant/Redis before the slice that needs them.

## Decisions

### D1 — Root `/src` modular monolith

**Choice:** Application code under `src/` at repo root; `alembic/`, `tests/`, `Dockerfile`, `pyproject.toml` at root; `frontend/` sibling.

**Why:** Single deployable API module; FE extractable later without a nested `backend/` rename churn.

**Alternatives:** `/backend` package (rejected — user preference); `apps/api` monorepo (defer).

### D2 — phase-slices as implementation SSOT per phase

**Choice:** Each slice folder holds `blueprint.md`, `guardrails.md`, `validation.md`, `references.md`.

**Why:** OpenSpec proposal/design stay lean; engineers open one slice folder when applying `pN-*`.

**Alternatives:** Only OpenSpec tasks (too thin for multi-week program); only bible (too fat for step proofs).

### D3 — Two-tier OpenSpec

**Choice:**

1. `phase-slices-program` (this change) — docs + fail-soft spec.
2. Later `p0-foundation`, `p1-chat`, … — code applies, each referencing its slice folder.

**Why:** Proposing “all slices” as blueprints now; applying all code at once would violate one-phase proofs.

**Alternatives:** One mega change with all code tasks (rejected).

### D4 — Validation gate

**Choice:** Each slice `validation.md` lists pytest/eval/CI checks. A phase is “done” only when those pass. Next phase OpenSpec apply should not start until the prior gate is green (process rule).

**Why:** User requirement: blueprint → test/validation → next.

### D5 — Fail-soft in every block

**Choice:** Spec `fail-soft-boundaries` + per-slice guardrails table mirroring bible failure kinds relevant to that slice.

**Why:** Absolute fallbacks are product trust (maps/POIs), not optional polish.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Blueprints rot before code | Keep slices short; update on apply; architecture-draft changelog |
| Too many OpenSpec changes later | One change per phase is intentional; don’t batch-apply |
| Docs-only apply feels empty | Proof = all slice files exist + openspec validate + README index |

## Migration Plan

1. Apply this change: write `phase-slices/**`, sync docs pointers, archive/sync `fail-soft-boundaries` when ready.
2. Propose/apply `p0-foundation` next for `/src` scaffold.
3. Continue phase-by-phase.

## Open Questions

1. Exact CI provider (GitHub Actions vs other) — choose in `p0-foundation`.
2. Whether guest **session draft** trips are DB-backed or cookie-only until auth — decide in `p1`/`p4` design.
