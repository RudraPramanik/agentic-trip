## Context

See `proposal.md` for why. P3 left confirmed `trip_scope`, catalog acquire/retrieve with PostGIS places, catalog HTTP, and session `catalog` JSONB. Session rows already have nullable `itinerary`, `validation`, `trip_id`, and `run` JSON fields. Ports `GenerateRunner` and `TravelEngine` exist as abstract stubs; `modules/planner` and `modules/trips` are empty shells; agents have dialogue/intent only. Frontend chat supports catalog acquire after scope — no Build plan yet.

Implementation follows `system-docs/phase-slices/p4-generate/` (P4.1–P4.11, guardrails, validation), `system-docs/llm.md` §7.4 / §8, `SHARED-SWE-LLD.md`, and `SHARED-FAIL-SOFT.md`. Call chain stays locked: routers → services/runner → ports/repos; generate graph calls services/ports only (no SQL, no vendor httpx inside graph nodes).

## Goals / Non-Goals

**Goals:**

- In-process `GenerateRunner` with progress events, cooperative abort, and wall-clock timeout.
- Pure `TravelEngine.pack` + travel matrix + `validate_itinerary`.
- Generate pipeline: retrieve → pack → validate → narrative → `persist_draft`.
- Product SSE generate + abort routes; FE Build plan CTA.
- Goldens + unit/ASGI proofs; local terminal and browser validation tasks.
- Reliability posture: bounded spend, catalog-grounded stops, draft-only persist, port seam for later ARQ.

**Non-Goals:**

- ARQ generate adapter; OR-Tools; LLM stop-order.
- Map/guidebook/PDF UI; revise; Explore; booking; OAuth save API.
- Wandr paths/DTOs/env; invented coords/POIs/polylines.
- Auto-generate on confirm_scope or every chat turn.

## Decisions

### D1 — InProcessGenerateRunner owns abort + timeout (P4.1, P4.8)

`InProcessGenerateRunner` implements `GenerateRunner.start(session_id)` / `abort(session_id)`. Per-session run state holds `abort_requested`, started-at, and an async event/queue for SSE consumers. Wall-clock timeout (settings env, e.g. `GENERATE_TIMEOUT_SECONDS`, freeze default in settings — propose **120s** for local, overridable) sets the same `abort_requested` flag. Stages check the flag between retrieve/pack/validate/narrative/persist; after abort/timeout, no success persist.

**Why in-process first:** architecture L17; Redis not required for generate.  
**Why not** request-thread blocking without a runner: need abort + multi-consumer SSE.  
**Alternative:** ARQ generate now. Rejected — blueprint non-goal; keep port for later.

### D2 — Domain itinerary types in planner (P4.2–P4.4)

Define `Itinerary`, `Day`, `Stop`, `ValidateResult` in `modules/planner` (Pydantic/dataclasses). `TravelEngine.pack(scope, places, prefs) -> Itinerary` is constrained greedy: sort candidates (preference/score then travel compactness), assign under day time/walk/transfer caps, hub sequence when `trip_scope.hubs` present. `travel_matrix` / `haversine_meters` supply times — OSRM table adapter optional; missing OSRM → haversine + penalty; **never** return fake LineString.

`validate_itinerary(itinerary, catalog_ids, scope) -> ValidateResult` is pure: id ∈ catalog, country filter, day caps, transfer sanity.

**Why pure code:** bible — structure from engine, not LLM.  
**Why greedy:** LLD §8 lock; OR-Tools later behind same port.  
**Complexity:** O(n log n) sort + linear assign.

### D3 — generate_graph orchestrates services (P4.5–P4.7)

`modules/agents/generate.py` nodes call:

1. `CatalogService.retrieve` (or PlaceRepository via catalog service)
2. `TravelEngine.pack`
3. `validate_itinerary`
4. `write_narrative` via `LlmGateway.complete(role="narrative", …)` — titles/stories only; strip any new ids
5. `TripService.persist_draft(session_id, itinerary, validation)` only if validate passed and not aborted

`TripService.persist_draft` writes session `itinerary` + `validation`, sets draft marker (`status=draft` inside itinerary JSON and/or `trip_id` pointing at an optional `trips` row with `status=draft`). Prefer **session JSONB draft first** (fields already exist) plus a thin `trips` table if blueprint types require a row — if both, keep single SSOT: draft body on session, `trips.status=draft` mirror only when needed for later save. Default assumption: **session itinerary JSONB with `status: "draft"`** is sufficient for P4; add `trips` table only if reopen/query needs it beyond session projection.

**Why graph nodes thin:** SHARED-SWE-LLD — agents call services.  
**Why draft not saved:** product law + Explore last-trip lock.

### D4 — Narrative id lock (P4.6)

`write_narrative` receives validated itinerary, asks LLM for titles/stories keyed by existing day/stop ids, merges text fields only. Post-condition assert: place-id set unchanged. On LLM unavailable/fail: persist validated structure without narrative **or** honest error — never invent stops. Prefer **persist structure without narrative** when validation already passed (better UX; still honest).

### D5 — HTTP SSE + abort (P4.9, P4.8)

`src/api/generate.py`:

- `POST /api/v1/sessions/{id}/generate` → ownership check → `GenerateRunner.start` → SSE (`text/event-stream`) emitting `progress` | `done` | `error` | `aborted`
- `POST /api/v1/sessions/{id}/generate/abort` → `{ "abort_requested": true }`

Disconnect: Starlette request disconnect detection sets abort. Router: parse/serialize + Depends only.

### D6 — FE Build plan CTA (P4.11)

After `trip_scope` present, show **Build plan** button. `startGenerate(sessionId)` consumes generate SSE (reuse/extend `frontend/lib/sse.ts`). Show progress text; on `done` refresh session projection; optional Abort control calling abort route. Catalog panel remains separate. No auto-generate on scope lock message.

### D7 — Timeout default and settings

Freeze `GENERATE_TIMEOUT_SECONDS` in settings (default **120**). Document in design/tasks; override via env for local long runs. Timeout shares abort path; SSE terminal event may include reason `timeout` inside `aborted`/`error` payload.

### D8 — Testing, goldens, local validation (P4.10 + SWE)

| Layer | Proof |
|-------|--------|
| Unit | runner progress + abort/timeout; pack catalog-only + day_budget; matrix no fake geometry; validate gates; narrative id lock; persist_draft refuse on fail |
| Integration | generate_graph with fakes: valid → draft; invalid → no persist |
| ASGI | generate SSE progress→done/fail; abort; ownership denied |
| Goldens | Meghalaya/Japan-shaped; Japan-10-days-or-HITL; border/country; abandoned; failed still traced (fake Obs) |
| Local terminal | Compose up → pytest subset → curl/httpx SSE smoke against local API |
| Local browser | scope confirm → catalog optional → Build plan → progress → draft visible; abort mid-run |
| CI | pytest includes these; failures block |

Prefer fakes: stub catalog retrieve, stub LLM narrative, no live OSRM.

### D9 — Error / fallback map (slice)

| Kind | Fallback |
|------|----------|
| Validation fail | No success persist; SSE error |
| Empty retrieve | Honest fail / no invent |
| Narrative LLM fail | Structure-without-narrative or honest fail; never new stop ids |
| OSRM missing | Haversine + penalty; no polyline |
| Abort / disconnect / timeout | Cooperative cancel; SSE aborted/error; no success persist |
| Obs down | No-op; generate still completes product path |

### D10 — Scalability / reliability / SWE posture (v1)

- **Bound spend:** wall-clock timeout + abort flag between stages.
- **Determinism:** pack/validate pure and unit-tested; scalable to larger catalogs via sort+assign (not combinatorial search).
- **Grounding:** catalog ids only → validate is O(stops) set membership.
- **Horizontal later:** `GenerateRunner` port allows ARQ adapter without route changes.
- **Idempotency:** re-generate replaces draft for session; abort flags safe to set twice; do not double-mark success after abort.
- **Layering:** routers → runner/services → ports; no God-service (TripService ≠ CatalogService ≠ ChatService).

## Risks / Trade-offs

- **[Risk] Greedy packer quality on thin catalogs** → Mitigation: honest empty/partial; validate caps; goldens with fixtures; no foreign refill.
- **[Risk] Long LLM narrative exceeds timeout** → Mitigation: timeout aborts; prefer structure-without-narrative; keep narrative last stage.
- **[Risk] In-process generate blocks worker capacity under load** → Mitigation: v1 single-user local; timeout; later ARQ behind same port.
- **[Trade-off] Session JSONB draft vs trips table** → Mitigation: start with session `itinerary.status=draft`; add trips row only if needed for reopen queries.
- **[Risk] FE auto-generate regression** → Mitigation: explicit CTA task + browser proof; chat path tests assert no generate.
- **[Trade-off] Persist without narrative on LLM fail** → Mitigation: documented fail-soft; user still gets grounded days.

## Migration Plan

1. Planner types + matrix + pack + validate + unit proofs.
2. Runner + abort/timeout + unit proofs.
3. TripService.persist_draft + generate_graph wiring + integration fakes.
4. Narrative helper + id-lock tests.
5. Mount generate/abort routes; ASGI SSE proofs.
6. Goldens + obs fail-soft traces.
7. FE Build plan + browser/terminal smoke.
8. Align `p4-generate/validation.md` checkboxes; resolve blueprint↔`llm.md` conflicts in-repo.

Rollback: feature is additive routes/CTA; disable by not mounting router / hiding CTA if needed. No Wandr coupling.

## Open Questions

- Exact default `GENERATE_TIMEOUT_SECONDS` beyond the proposed 120s can be tuned during apply without changing specs (keep abort-path semantics).
- Whether a separate `trips` table row is required in P4 vs session JSONB-only will be decided at persist_draft implementation by the smallest change that satisfies draft reopen + `status=draft` proofs.
