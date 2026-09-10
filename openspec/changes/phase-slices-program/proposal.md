## Why

Architecture is settled, but implementation needs a **shared delivery contract**: root modular monolith layout (`/src` + `/frontend`), **per-phase blueprints** with fail-soft guardrails, and a **validate/CI gate** before the next slice. Capturing all phase-slice blueprints now prevents context loss and keeps later `/opsx-apply` work scoped and honest.

## What Changes

- **Work type: docs / cross-cutting planning** (no application feature code in this change’s apply beyond writing `phase-slices/` and aligning `system-docs`).
- Lock **repo layout**: FastAPI modular monolith at repo root under `/src` (not `/backend`); `/alembic`, `/tests`, `/frontend`, `/system-docs`, `/phase-slices` at root.
- Author **`phase-slices/<id>/`** packages for **all** phases (P0–P9 + P5b): blueprint, guardrails, validation, references.
- Codify **fail-soft / error-boundary** as a first-class capability (named fallback per external kind; no hang/hallucinate).
- Define delivery loop: **blueprint → implement (later change) → tests/CI validation → next phase**.
- Align `system-docs/architecture-draft.md` (already updated in exploration) as the settled pointer.

### Non-goals

- Implementing `/src` FastAPI app, Docker images, or Next.js features in this change (that is `p0-foundation` and later phase OpenSpec changes).
- Live booking, OAuth, Qdrant, PDF rendering, or media enrich code.
- Inventing Wandr endpoints, DTOs, or env vars.
- Microservices split; FE repo split (FE stays `/frontend` for now).

## Capabilities

### New Capabilities

- `fail-soft-boundaries`: Every external/IO kind (geocoder, catalog/retrieve, LLM, routing, GPS/IP, workers, observability) MUST have a named fallback; failures MUST NOT become unbounded hangs or hallucinated map/POI facts.

### Modified Capabilities

- (none — product intake/planner/explore/booking behavior unchanged; this change adds cross-cutting fail-soft law and delivery docs)

## Impact

- **Docs:** `phase-slices/**`, `system-docs/architecture-draft.md`, `system-docs/README.md` / system-map pointers.
- **OpenSpec:** New main capability `fail-soft-boundaries` after archive/sync; per-phase **code** changes remain separate (`p0-foundation`, `p1-chat`, …).
- **Future code:** Root `/src` modular monolith + CI validation gates per slice; no Wandr coupling.
