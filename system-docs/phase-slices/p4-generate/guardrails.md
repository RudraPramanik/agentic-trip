# P4 Generate + engine + validate — guardrails

Start from [`../SHARED-FAIL-SOFT.md`](../SHARED-FAIL-SOFT.md) and [`../SHARED-SWE-LLD.md`](../SHARED-SWE-LLD.md).

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| Validation fail | Do not persist successful trip |
| LLM narrative fail | Structure may still save if valid; or honest fail — never invent stops |
| Abort | No unbounded continuation |
| Model invents venue | Not scheduled |
| Routing times missing | Haversine + penalty; no fake polylines |

## SWE / LLD delta

- `pack_days` and `validate_itinerary` are **pure code**; LLM must not choose stop order or coords.
- Travel times: OSRM table or `haversine_meters` + penalty — never crow-flies geometry as map facts.
- `GenerateRunner` in-process SSE (L17); ARQ later behind the same port.
- Graphs call services/ports only; no SQL in generate_graph.
- Abort = disconnect + `abort_requested`; not HITL interrupt.

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
