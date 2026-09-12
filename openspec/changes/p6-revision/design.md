## Context

See `proposal.md` for why. P4 shipped `InProcessGenerateRunner`, `run_generate` (retrieve → pack → validate → narrative → `persist_draft`), generate SSE + abort, and a FE Build plan CTA. P5/P5b shipped trip get/export, MapLibre points, guidebook, and FE print/PDF. Session rows already have `itinerary`, `validation`, `trip_id`, `run`, and `budget` (`dialogue | generate | revise`). There is no `revise.py`, no cap checker, no `/revise` route, and chat send still always hits `/messages`.

Implementation follows `system-docs/phase-slices/p6-revision/` (P6.1–P6.5, guardrails, validation), `system-docs/llm.md` §7.5, `SHARED-SWE-LLD.md`, and `SHARED-FAIL-SOFT.md`. Call chain stays locked: routers → services/runner → ports/repos; `revise_graph` calls services/ports only (no SQL, no vendor httpx inside graph nodes).

## Goals / Non-Goals

**Goals:**

- Structured revision intent + mandatory caps before another expensive generate.
- `revise_graph` re-enters the existing generate pipeline (same engine, validate, draft persist).
- Product SSE revise route; FE Revise plan CTA; structure + guidebook + map update.
- Goldens + unit/ASGI proofs; local terminal, Playwright e2e, and apply-time Playwright MCP validation.
- Reliability posture: bounded loops, cooperative abort/timeout reuse, catalog-grounded stops, replace-in-place draft, port seam for later ARQ.

**Non-Goals:**

- New TravelEngine algorithm; OR-Tools; LLM stop-order; unconstrained prose rewrite.
- Raising caps silently; booking vendor (P8); Explore (P7); OAuth save API.
- Wandr paths/DTOs/env; invented coords/POIs/polylines.
- Auto-revise on every chat turn.

## Decisions

### D1 — Structured `RevisionIntent` via dialogue-role LLM (P6.1)

`parse_revision_intent(text, itinerary) -> RevisionIntent` lives in `src/modules/agents/revise.py`. Call `LlmGateway.complete(role="dialogue", …, schema=RevisionIntent)`. Intent is a **patch**, not a new itinerary:

- Optional `day_index` (1-based, must exist on current itinerary)
- Walk/pace: `walk_budget_factor` (< 1 means less walking) and/or `max_stops_per_day`
- Optional `drop_place_ids` only when those ids already appear on the itinerary
- Optional tag/category prefs for pack sort
- `unknown_names[]` recorded then **ignored** (never scheduled)

When the gateway is unavailable or schema parse fails: deterministic heuristics for the golden phrase family (“less walking” + optional “day N”) so CI/fakes stay green; otherwise honest error — never a prose rewrite of days.

**Why LLM + schema:** architecture `revise_graph` is “Yes + code”; dialogue role already exists.  
**Why not** free-form rewrite: product law + blueprint non-goal.  
**Alternative:** regex-only parser. Rejected as sole path — too brittle for drop-a-stop / swap-day — keep heuristic as fail-soft, not the only implementation.

### D2 — Cap checker is a hard gate (P6.2)

`src/modules/planner/caps.py`: `ReviseCaps` + `check_caps(state) -> Ok | StopAndExplain`.

Freeze on the **first successful generate** (or first revise if missing):

- `baseline.max_stops_per_day`, `baseline.day_travel_budget_s`, `baseline.day_budget`
- Stored on `session.run` or `session.itinerary.revise_baseline` (JSON; no new table required)

Each revise attempt:

1. Increment `revise_loop_count` (proposed, not committed until a successful persist — failed/capped attempts still count toward the loop budget so retries cannot burn unbounded LLM)
2. If `revise_loop_count > REVISE_MAX_LOOPS` (settings, default **3**) → `StopAndExplain`, keep last valid
3. If the patch would **raise** walk/day/stop budgets above baseline → `StopAndExplain` (do not enlarge silently)
4. Else `Ok` with merged prefs

**Why snapshot baseline:** “never raise caps silently” needs a reference.  
**Why count failed attempts:** otherwise a hostile/looping client burns generate on validation-fail retries.  
**Alternative:** count only successful persists. Rejected — weaker spend bound.

### D3 — Per-day pack prefs, not a new packer (P6.3)

Extend existing `pack_days` prefs with optional `day_overrides: { <day_index>: { max_stops_per_day, day_travel_budget_s } }`. Default path unchanged. “Less walking day 2” → lower day 2 travel budget and/or max stops (e.g. factor 0.6 / max_stops 2). `drop_place_ids` filter the retrieve/pack candidate set. Hub sequence and country filter stay as P4.

`run_revise` nodes: parse → caps → merge prefs into session intent/run → **reuse** `run_generate` stages (retrieve → pack → validate → narrative → persist). Do not fork a second pipeline. Graph/nodes call services/ports only.

**Why extend prefs:** smallest change that makes the golden structurally observable.  
**Why reuse `run_generate`:** blueprint “re-enter generate”; one validate/persist implementation.  
**Alternative:** new TravelEngine. Rejected — explicit non-goal.

### D4 — Replace-in-place draft persist

On validation success, `TripService.persist_draft` already overwrites session itinerary and the trips row for `state.trip_id`. Keep the same `trip_id` and `status=draft`. Set `state.budget = "revise"` during the run; restore `dialogue` after terminal. Do not create a second trip row. Booking placeholder stays hollow (no rates).

If validation fails or abort/timeout: do not write the new itinerary; last valid session + trip artifact remain.

**Why same trip_id:** guidebook/map/PDF already keyed by trip; FE can refetch export.  
**Alternative:** versioned trip rows. Rejected for v1 — extra schema, Explore still locked.

### D5 — HTTP SSE reuses generate runner abort/timeout (P6.4)

`src/api/revise.py` (preferred over stuffing sessions.py):

- `POST /api/v1/sessions/{id}/revise` body `{ "text" }` → ownership check → runner `start_revise(session_id, text)` → SSE `progress` | `done` | `error` | `aborted`
- Cap-stop is a terminal `error` (or `done` with `capped: true` **rejected** — must be honest error/stop, last valid kept)
- Disconnect → `runner.abort(session_id)`
- In-flight abort: existing `POST .../generate/abort` stops the session’s expensive run (generate **or** revise). No second abort path unless apply finds a naming collision — then add `POST .../revise/abort` as a thin alias to the same flag.

Timeout: reuse `GENERATE_TIMEOUT_SECONDS` **or** `REVISE_TIMEOUT_SECONDS` default 120 (same abort path). Redis not required. Router: parse/serialize + Depends only.

Extend `InProcessGenerateRunner` with `start_revise` (same `_RunState` / queue / watchdog). Do not allow generate and revise concurrently on one session: if a run is in-flight, refuse the other with an honest error.

**Why SSE:** same abort/progress UX as generate; LLD “SSE or result”.  
**Why reuse abort route:** one cooperative flag; specs require shared abort path.  
**Alternative:** JSON 200 with final itinerary. Rejected — no progress/abort story.

### D6 — FE Revise plan after draft (P6.4 + workingness)

After `draft.status === "draft"`, show **Revise plan** in the chat shell. Composer text + Revise plan → `postRevise` + existing `readSse`. On `done`: `refreshSession` + `loadGuidebook(tripId)` so guidebook days and MapLibre points update. Show progress; Abort control reuses generate abort. Cap-hit / error: honest line in chat; previous draft/guidebook/map remain.

Ordinary Send still `POST .../messages` and MUST NOT call revise. Build plan still generate-only.

Playwright: add `frontend/e2e/revise-plan.spec.ts`. Prefer a **seeded/fixture session** (or page that injects a draft + stubbed revise SSE) so CI does not need a live LLM. During **apply**, additionally walk the live stack with Playwright MCP: draft visible → type “less walking day 2” → Revise plan → progress → structure/map change (or honest cap/error if catalog thin — then fix until the happy path works locally).

**Why explicit CTA:** architecture “generate/replan only on explicit update plan”; cheap dialogue stays cheap.  
**Alternative:** auto-route every post-draft chat to `/revise`. Rejected — violates “not every chat turn”.

### D7 — Settings

| Setting | Default | Notes |
|---------|---------|--------|
| `REVISE_MAX_LOOPS` | **3** | Inclusive attempts per session draft; env-overridable |
| `REVISE_TIMEOUT_SECONDS` | **120** | May alias generate timeout in code if identical |

Document names only in `.env.example` / `.env.demo`. Never commit secrets.

### D8 — Testing, goldens, local validation (P6.5 + SWE)

| Layer | Proof |
|-------|--------|
| Unit | “less walking day 2” → walk-cap patch; unknown venue ignored; cap hit → stop + last valid unchanged; silent raise refused |
| Integration | revise_graph with fakes: structure changes; map/export stop ids follow; validation fail → no persist |
| ASGI | revise SSE progress→done; cap error; abort; foreign session denied; Redis down does not block |
| Golden | less-walking-day-2 updates structured itinerary within cap; validation still required to persist |
| Playwright | Revise plan visible after draft; send does not revise; successful revise refreshes guidebook/map (fixture or stub) |
| Local terminal | Compose up → pytest subset → httpx/curl `POST .../revise` SSE through done; abort mid-run keeps last valid |
| Apply-time | Playwright MCP against local frontend for the real feature path |
| CI | pytest + frontend unit + Playwright smoke; failures block |

Prefer fakes: stub LLM intent (or heuristic), stub catalog retrieve, no live OSRM.

### D9 — Error / fallback map (slice)

| Kind | Fallback |
|------|----------|
| Loop / walk / day cap | Stop and explain; keep last valid |
| Validation fail on replan | Do not save invalid as success |
| Unknown venue in text | Ignore; never schedule |
| LLM intent unavailable | Heuristic for known phrases; else honest error |
| Empty retrieve | Honest fail; last valid kept |
| Narrative LLM fail | Structure-without-narrative or honest fail; never new stop ids |
| Abort / disconnect / timeout | Cooperative cancel; last valid kept |
| Obs down | No-op; revise still completes product path |
| Concurrent generate+revise | Honest refuse; do not interleave pack |

### D10 — Scalability / reliability / SWE posture (v1)

- **Bound spend:** caps before generate + loop count includes failed attempts + wall-clock timeout + abort between stages.
- **Determinism:** pack/validate remain pure; per-day overrides are O(1) lookups; complexity still O(n log n) sort + linear assign.
- **Grounding:** catalog ids only; unknown names never become stops.
- **Horizontal later:** same `GenerateRunner` port allows ARQ without route changes.
- **Idempotency:** replace-in-place on `trip_id`; abort flags safe to set twice; do not persist success after abort/cap.
- **Layering:** routers → runner/services → ports; no God-service (`revise` ≠ ChatService ≠ CatalogService). Agents call services/ports only.
- **Single gateways:** `LlmGateway` + existing geo/catalog ports; no new vendor.

## Risks / Trade-offs

- **[Risk] Heuristic + LLM disagree on intent** → Mitigation: schema-first LLM; heuristic only when gateway unavailable; golden locked to structured walk-cap outcome.
- **[Risk] Thin catalog: “less walking” cannot change day 2** → Mitigation: fixture catalogs in unit/golden/Playwright; local MCP run uses seeded catalog; honest fail if pack cannot apply patch.
- **[Risk] Counting failed revises toward the loop cap feels strict** → Mitigation: default 3 is enough for local demo; env-tunable; message explains remaining attempts.
- **[Risk] Reusing generate abort name confuses clients** → Mitigation: document shared expensive-run abort; add `/revise/abort` alias if FE/tests need it.
- **[Risk] In-process revise blocks under load** → Mitigation: v1 single-user local; timeout + caps; later ARQ behind same port.
- **[Trade-off] Explicit Revise plan vs auto-chat routing** → Mitigation: specs require explicit action; chat remains cheap.
- **[Trade-off] Per-day overrides vs global walk factor** → Mitigation: support both; golden uses day-scoped override.

## Migration Plan

1. `RevisionIntent` + parse (LLM schema + heuristic) + unit proofs.
2. `ReviseCaps` / `check_caps` + baseline snapshot + unit proofs.
3. Per-day pack prefs; `run_revise` wrapping `run_generate`; persist replace-in-place.
4. Mount revise SSE; wire runner `start_revise`; shared abort/timeout; ASGI proofs.
5. Golden less-walking-day-2 + obs fail-soft.
6. FE Revise plan + refresh guidebook/map; Playwright e2e.
7. Local terminal SSE smoke + apply-time Playwright MCP walkthrough.
8. Align `p6-revision/validation.md` checkboxes; resolve blueprint↔`llm.md` conflicts in-repo.

Rollback: additive route/CTA; disable by not mounting revise router / hiding CTA. No Wandr coupling. Existing generate/guidebook/PDF clients unchanged.

## Open Questions

- Exact default `REVISE_MAX_LOOPS` / timeout seconds beyond 3 and 120 can be tuned during apply without changing specs (keep cap-stop and abort-path semantics).
- Whether apply adds `POST .../revise/abort` as a documented alias is a naming convenience only (same `abort_requested` flag).
