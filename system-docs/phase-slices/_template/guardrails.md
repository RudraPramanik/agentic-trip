# <Slice> — guardrails

Start from [`../SHARED-FAIL-SOFT.md`](../SHARED-FAIL-SOFT.md) and [`../SHARED-SWE-LLD.md`](../SHARED-SWE-LLD.md), then add slice-specific rows.

## Fail-soft table

| Kind | Fallback |
|------|----------|
| | |

## SWE / LLD delta

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Follow shared algorithm locks and naming in `SHARED-SWE-LLD.md`.
- (Add slice-specific architecture / algorithm / consistency rules here.)

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.

## Non-goals
