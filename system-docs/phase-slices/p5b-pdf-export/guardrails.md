# P5b PDF / print export — guardrails

Start from [`../SHARED-FAIL-SOFT.md`](../SHARED-FAIL-SOFT.md) and [`../SHARED-SWE-LLD.md`](../SHARED-SWE-LLD.md).

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| Export DTO incomplete | Fail with clear error; do not invent hotels/prices |
| Render failure | User-visible error; trip data intact |

## SWE / LLD delta

- PDF/print is a pure projection of `GuidebookExport`.
- No `LlmGateway` on the PDF path.
- No fake booking rates in the document.
- Optional `GET /api/v1/trips/{id}/pdf` is this product’s path — not Wandr.

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
