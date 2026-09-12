# phase-slices

Per-phase implementation packages for **agentic-trip**.  
Settled architecture: [`../architecture-draft.md`](../architecture-draft.md)  
Product goal: [`../product-goal.md`](../product-goal.md)  
LLD SSOT: [`../llm.md`](../llm.md)  
Shared fail-soft: [`SHARED-FAIL-SOFT.md`](./SHARED-FAIL-SOFT.md)  
Shared SWE / LLD: [`SHARED-SWE-LLD.md`](./SHARED-SWE-LLD.md)

## Delivery loop

```
blueprint.md (P{n}.1, P{n}.2, …)  →  implement one sub-phase  →  sub-phase proof
        │                                    │
        └──── guardrails (fail-soft + SWE/LLD) + llm.md ────┘
                     ↓
              validation.md (all sub-phases + phase CI)  →  next slice
```

**Next code change after this program:** propose/apply **`p0-foundation`** (scaffold `/src` as P0.1 → P0.12 — not done in docs-only LLD changes).

## Catalog

| Slice | OpenSpec change (later) | Sub-phases | Proof (summary) |
|-------|-------------------------|------------|-----------------|
| [p0-foundation](./p0-foundation/) | `p0-foundation` | P0.1–P0.12 | Health + CI smoke; module shells incl. `monitor`/`evals` |
| [p1-chat](./p1-chat/) | `p1-chat` | P1.1–P1.9 | Guest SSE round-trip |
| [p2-dialogue-scope](./p2-dialogue-scope/) | `p2-dialogue-scope` | P2.1–P2.9 | Scope/HITL goldens |
| [p3-catalog](./p3-catalog/) | `p3-catalog` | P3.1–P3.8 | Acquire + PostGIS retrieve |
| [p4-generate](./p4-generate/) | `p4-generate` | P4.1–P4.11 | SSE generate + validate + timeout + Build plan CTA |
| [p5-guidebook-map](./p5-guidebook-map/) | `p5-guidebook-map` | P5.1–P5.6 | Map + guidebook + export DTO |
| [p5b-pdf-export](./p5b-pdf-export/) | `p5b-pdf-export` | P5b.1–P5b.4 | PDF/print from DTO |
| [p6-revision](./p6-revision/) | `p6-revision` | P6.1–P6.5 | Capped replan |
| [p7-explore](./p7-explore/) | `p7-explore` | P7.1–P7.5 | Near me + last-trip **locked on draft** |
| [p8-booking-placeholder](./p8-booking-placeholder/) | `p8-booking-placeholder` | P8.1–P8.5 | Hollow stays |
| [p9-hardening](./p9-hardening/) | `p9-hardening` | P9.1–P9.5 | Eval CI gate + caps |

## Package files

Each slice contains: `blueprint.md`, `guardrails.md`, `validation.md`, `references.md`.  
New slices: copy [`_template/`](./_template/).

## Follow-on OpenSpec names (implementation)

`p0-foundation` → `p1-chat` → `p2-dialogue-scope` → `p3-catalog` → `p4-generate` → `p5-guidebook-map` → `p5b-pdf-export` → `p6-revision` → `p7-explore` → `p8-booking-placeholder` → `p9-hardening`

Execute each **code** change as numbered sub-phases inside that slice’s blueprint, using [`../llm.md`](../llm.md).
