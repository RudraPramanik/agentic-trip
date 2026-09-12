## Context

See `proposal.md` for why. Phase-slice packages, `system-docs/llm.md`, and `system-docs/product-goal.md` already describe P0–P9. Several product laws have no owner sub-phase. This change is docs-only: assign owners and clarify v1 semantics. No `/src` or `frontend/` edits.

Constraints: single LLM/geo gateways; generate abortable; no invented coords, venues, or polylines; no Wandr contracts; no twelfth product phase.

## Goals / Non-Goals

**Goals:**

- One named owner sub-phase + proof per law in the `phase-slice-lld` delta.
- Same owner names in `llm.md` as in the slice blueprints.
- Bible eval table becomes the P2/P4/P9 golden checklist.

**Non-Goals:**

- Implementing generate, OAuth, Explore, or timeout in code.
- Adding `POST` save or a polyline producer.
- Renumbering the whole P0–P9 catalog or adding `p10-*`.

## Decisions

### 1. V1 artifact = guest draft; last-trip stays locked

**Choice:** Document two statuses: `draft` (guest session, reopenable in-cookie) and `saved` (authenticated, Later / OAuth). P4 `persist_draft` produces `draft` only. P7 last-trip unlocks only on `saved`. Tests for the saved branch use a fixture row, not a fake OAuth user on prod paths.

**Why not** treat draft as saved: that would unlock last-trip and trip-keyed booking from a cookie, contradicting L18 and `explore-geo-feed`.

**Why not** add OAuth in this change: architecture already parks it in Later; this change only stops implementers from inventing it.

### 2. Explicit generate CTA lives in P4, not P1

**Choice:** Keep P1.8 non-goal (no generate button). Add **P4.11 — FE generate CTA**: after `trip_scope` is confirmed, chat shows a Build plan control that calls existing `POST /api/v1/sessions/{id}/generate`. Confirming scope (P2.7) still only explains scope.

**Why not** auto-generate on `confirm_scope`: breaks the two-budget law.

**Why not** a new HTTP resource: the generate route already exists in the LLD.

### 3. Wall-clock timeout is a P4 behavior; P9 only hardens

**Choice:** Fold timeout into **P4.1 / P4.8** (same abort path: set `abort_requested`, no success persist, honest SSE `aborted` or `error`). Add the kind to shared fail-soft. P9.3 may make the flag durable across workers; it MUST NOT introduce timeout as new product behavior.

Exact seconds stay env-tunable and are frozen in the later `p4-generate` design.

**Why not** P9-only: principle 4 is a generate-path law; waiting until hardening invites unbounded P4 runs.

### 4. Country-long hubs stay in P2; no new slice

**Choice:** Extend **P2.4 / P2.9**: country + longer than the short threshold writes `hubs[]` or HITL. P3.3 already refuses country-without-hubs. P4.10 asserts a Japan-10-days-shaped (or HITL) itinerary.

**Why not** invent hubs in P4: scope identity is a dialogue/geo job.

### 5. Goldens: extend lists, do not invent a new harness module

**Choice:** P2.9 and P4.10 (and P9.5 as the CI union) MUST name every bible case. Failed-generate-still-traced is a P4 proof (obs fake or no-op). Tuscany-style region, Kyoto-wins, border filter, missing duration move from “implied” to listed checkboxes.

### 6. Explore leftovers stay in P7

**Choice:** Extend P7.2 (draft ≠ saved), P7.4 (tab anchors + plan-from-card + IP approximate copy), P7.5 proofs. No new Explore slice.

### 7. Clarifications without new phases

| Topic | Owner note |
|-------|------------|
| Map geometry | P5.4 + bible: v1 is **points only** unless a later slice stores route geometry. Do not invent crow-flies. |
| Retrieve fallback | Shared fail-soft: “geo fallback” means PostGIS when a later vector index is empty/down. P3 retrieve *is* PostGIS; empty → honest empty + HITL at generate. |
| Live LLM adapter | Fold `LiteLlmAdapter` into **P2.1** (keys present → live; missing → existing stub). Do not add P2.10. |

## Risks / Trade-offs

- [Last-trip always locked in v1] → Users may think Explore is broken. Mitigation: P7 copy states a saved plan unlocks it; do not silently fill from draft.
- [Timeout seconds unspecified] → P4 implementers pick a number. Mitigation: env setting; freeze in `p4-generate` design, not here.
- [Adding P4.11] → P4 validation checklist grows. Mitigation: one new row; do not renumber P4.1–P4.10.
- [Docs drift if only slices change] → Edit product-goal, architecture L18 footnote, llm.md, and slices in the same apply.

## Migration Plan

1. Apply this change as docs edits only.
2. Then propose/apply `p0-foundation` against the updated slices.
3. Rollback = revert the docs commit; no runtime state.

## Open Questions

- Default generate timeout seconds (ops/env; freeze in `p4-generate`).
- Exact OAuth provider when the Later auth phase starts (already an architecture open item).
