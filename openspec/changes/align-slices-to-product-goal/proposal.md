## Why

The phase-slice program covers the chat-first trip OS in `system-docs/product-goal.md`, but six product laws have no named owner sub-phase. Starting `p0-foundation` now would let later implementers invent save semantics, generate UX, timeouts, and goldens. Close those contracts in docs before any application code.

## What Changes

Docs-only. No new product phase. No `/src` or `frontend/` code.

- State **v1 save vs draft**: guest `persist_draft` is the reopenable artifact; authenticated save and last-trip unlock stay **Later (OAuth)**; last-trip stays locked through P0–P9.
- Assign an **explicit generate CTA** (Build plan) to a P4 sub-phase so generate never rides every chat turn.
- Assign a **wall-clock generate timeout** to P4 (P9 hardens only).
- Extend P2/P4 proofs for **country-long hubs** (Japan 10 days / HITL) so P3 acquire is not refused.
- Align P2.9 / P4.10 / P9 goldens with the bible eval table, including failed-generate still traced.
- Complete P7 leftovers already in `explore-geo-feed`: plan-from-card, tab-anchor independence, IP approximate copy.
- Clarify (no new phase): v1 maps are points-only; PostGIS retrieve *is* geo (vector fallback later); live `LiteLlmAdapter` lands in P2.

**BREAKING:** none (no shipped product API yet). Spec deltas clarify v1 behavior that was implied, not implemented.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `conversational-trip-planner`: v1 draft is reopenable without OAuth; generate starts only from an explicit user action; wall-clock generate timeout aborts the run.
- `explore-geo-feed`: last-trip stays locked until an authenticated saved trip exists (not a guest draft).
- `fail-soft-boundaries`: named fallback for generate timeout (stop spend, no success persist, honest outcome).
- `phase-slice-lld`: every product-goal law listed above MUST have a named owner sub-phase and proof in the slice packages.

## Impact

- **Docs:** `system-docs/product-goal.md`, `system-docs/llm.md`, `system-docs/architecture-draft.md` (L18 / goldens / API notes), `system-docs/phase-slices/` (P2, P4, P7, P9 plus shared SWE/fail-soft and README as needed).
- **OpenSpec main specs:** the four capabilities above, after archive/sync.
- **Code / APIs / infra:** none in this change. Later `p0-foundation` and following slices implement the clarified contracts.
- **Non-goals:** no Wandr endpoints, DTOs, or env vars; no OAuth; no live booking; no polyline inventor; no Qdrant-required retrieve; no twelfth product phase.
