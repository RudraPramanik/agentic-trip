# P8 Booking placeholder — guardrails

Start from [`../SHARED-FAIL-SOFT.md`](../SHARED-FAIL-SOFT.md) and [`../SHARED-SWE-LLD.md`](../SHARED-SWE-LLD.md).

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| Any vendor call attempted | Must not in this slice — non-goal |

## SWE / LLD delta

- Hollow module: no lodging/flight/activity vendor SDKs.
- Never invent rates, availability, or hotel names not in catalog (catalog is not booking).
- `BookingService` is read-only placeholder; keep it off dialogue and generate graphs.
- HTTP: `GET /api/v1/trips/{id}/booking` only for this product.

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
