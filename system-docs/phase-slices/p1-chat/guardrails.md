# P1 Chat — guardrails

Start from [`../SHARED-FAIL-SOFT.md`](../SHARED-FAIL-SOFT.md) and [`../SHARED-SWE-LLD.md`](../SHARED-SWE-LLD.md).

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| LLM dialogue down | Honest error message in stream; session intact |
| Client disconnect | Stop work for that turn |
| Invalid session | Issue new guest session; do not leak another user |

## SWE / LLD delta

- Cookie `AuthPort` only; never trust client-supplied `user_id` as identity.
- SSE send must abort on disconnect (cooperative cancel).
- `ChatService.send_message` must not call `GenerateRunner` or catalog acquire.
- Routers parse HTTP only; streaming owned by service + ASGI response.
- Chat traces: one trace per turn; missing obs backend = no-op.

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
