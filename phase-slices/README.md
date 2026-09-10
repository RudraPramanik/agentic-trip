# phase-slices

Per-phase implementation packages for **agentic-trip**.  
Settled architecture: [`../system-docs/architecture-draft.md`](../system-docs/architecture-draft.md)  
Product bible: [`../system-docs/chat-first-trip-os.md`](../system-docs/chat-first-trip-os.md)  
Shared fail-soft: [`SHARED-FAIL-SOFT.md`](./SHARED-FAIL-SOFT.md)

## Delivery loop

```
blueprint.md  →  (OpenSpec pN apply / code)  →  validation.md gate  →  next slice
                     ↑
              guardrails.md (fail-soft)
```

**Next code change after this program:** propose/apply **`p0-foundation`** (scaffold `/src` — not done in `phase-slices-program`).

## Catalog

| Slice | OpenSpec change (later) | Proof (summary) |
|-------|-------------------------|-----------------|
| [p0-foundation](./p0-foundation/) | `p0-foundation` | Health + CI smoke; module shells incl. `monitor`/`evals` |
| [p1-chat](./p1-chat/) | `p1-chat` | Guest SSE round-trip |
| [p2-dialogue-scope](./p2-dialogue-scope/) | `p2-dialogue-scope` | Scope/HITL goldens |
| [p3-catalog](./p3-catalog/) | `p3-catalog` | Acquire + PostGIS retrieve |
| [p4-generate](./p4-generate/) | `p4-generate` | SSE generate + validate |
| [p5-guidebook-map](./p5-guidebook-map/) | `p5-guidebook-map` | Map + guidebook + export DTO |
| [p5b-pdf-export](./p5b-pdf-export/) | `p5b-pdf-export` | PDF/print from DTO |
| [p6-revision](./p6-revision/) | `p6-revision` | Capped replan |
| [p7-explore](./p7-explore/) | `p7-explore` | Near me + last-trip |
| [p8-booking-placeholder](./p8-booking-placeholder/) | `p8-booking-placeholder` | Hollow stays |
| [p9-hardening](./p9-hardening/) | `p9-hardening` | Eval CI gate + caps |

## Package files

Each slice contains: `blueprint.md`, `guardrails.md`, `validation.md`, `references.md`.  
New slices: copy [`_template/`](./_template/).

## Follow-on OpenSpec names (implementation)

`p0-foundation` → `p1-chat` → `p2-dialogue-scope` → `p3-catalog` → `p4-generate` → `p5-guidebook-map` → `p5b-pdf-export` → `p6-revision` → `p7-explore` → `p8-booking-placeholder` → `p9-hardening`
