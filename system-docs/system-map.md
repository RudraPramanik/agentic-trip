# System map — agentic-trip

> Sibling product to Wandr. Behavior SSOT: [`chat-first-trip-os.md`](./chat-first-trip-os.md).  
> Settled architecture: [`architecture-draft.md`](./architecture-draft.md).  
> Phase blueprints: [`../phase-slices/`](../phase-slices/).

```
frontend/ (Next.js)                   src/ (FastAPI modular monolith @ repo root)
┌─────────────────────┐               ┌────────────────────────────────┐
│ Chat · Map · Guide  │── HTTP/SSE ──▶│ Orchestrator                   │
│ Explore             │               │  dialogue_graph | generate     │
└─────────────────────┘               │ modules/* service-separated    │
                                      │ ARQ worker (long jobs)         │
                                      └────────┬───────────────────────┘
                                               │
                         ┌─────────────────────┼─────────────────────┐
                         ▼                     ▼                     ▼
                    Postgres/PostGIS      Redis (ARQ)         Qdrant (later)
```

**Layout:** `/src` + `/alembic` + `/tests` + `/frontend` + `/phase-slices` + `/system-docs`  
**Save rule:** guest continues; durable trip/explore saves need auth (OAuth later).  
**Delivery:** each `phase-slices/pN` → implement → validation/CI → next.
