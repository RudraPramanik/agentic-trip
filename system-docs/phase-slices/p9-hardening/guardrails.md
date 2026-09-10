# P9 Hardening — guardrails

Start from [`../SHARED-FAIL-SOFT.md`](../SHARED-FAIL-SOFT.md) and [`../SHARED-SWE-LLD.md`](../SHARED-SWE-LLD.md).

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| Eval failure | CI fails; do not ship |
| Cost cap | Stop further LLM calls for run |
| Tracer unconfigured | No-op; product path still works |
| Redis down (rate limit) | Documented fail-soft or fail-closed; never hang |

## SWE / LLD delta

- Observability remains fail-soft: missing Langfuse must not crash requests.
- Cost caps wrap `LlmGateway`, not routers.
- Rate limit is middleware; keep business rules in services.
- Abort flag must be honored across workers if multi-instance.
- Evals live in `modules/evals`; do not block interactive requests mid-turn except caps/abort/rate-limit.

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
