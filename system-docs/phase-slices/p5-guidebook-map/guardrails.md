# P5 Guidebook UI + map + export DTO — guardrails

Start from [`../SHARED-FAIL-SOFT.md`](../SHARED-FAIL-SOFT.md) and [`../SHARED-SWE-LLD.md`](../SHARED-SWE-LLD.md).

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| No routing geometry | Points only |
| Map style fail | List-first fallback |
| Missing media | Category/gradient honest fallback — not fake venue photo claim |

## SWE / LLD delta

- Guidebook UI and PDF share `GuidebookExport` — no second narrative pipeline.
- Map: points always; polylines only when routing geometry exists.
- Media facade off generate hot path.
- Export is a mapping function, not an LLM rewrite of days/stops.

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
