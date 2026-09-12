# P5b PDF / print export — blueprint

> Status: implemented via OpenSpec `p5b-pdf-export` (FE print CSS + `@react-pdf/renderer` from GuidebookExport; no server PDF).  
> LLD: [`../../llm.md`](../../llm.md) §5 (FE print/PDF chosen; `GET .../pdf` deferred)

## Goal

PDF or print from GuidebookExport DTO only; no LLM inventing PDF content.

## Scope / modules

frontend print/react-pdf; optional ARQ render later

## Step plan

Implement **one sub-phase at a time**.

### P5b.1 — Print CSS from export DTO

- **Goal:** Browser print stylesheet consuming the same export JSON.
- **Modules:** `frontend/` print CSS / print view
- **Types:** `PrintGuidebook` / `GuidebookExportProjection`
- **Functions:** render export → print
- **Services:** none
- **Routes / APIs:** uses `GET /api/v1/trips/{id}/export`
- **Algorithms / data:** —
- **Depends on:** P5.1
- **Proof:** print preview matches saved days/stops fixture
- **Non-goals:** LLM copy for PDF

### P5b.2 — react-pdf (optional)

- **Goal:** Same DTO → `@react-pdf/renderer` if print CSS is not enough.
- **Modules:** `frontend/` pdf renderer
- **Types:** PDF document components
- **Functions:** `renderGuidebookPdf(export)`
- **Services:** none
- **Routes / APIs:** none required
- **Algorithms / data:** —
- **Depends on:** P5b.1 or P5.1
- **Proof:** fixture DTO → PDF without extra venues
- **Non-goals:** ARQ render job (later optional)

### P5b.3 — Download/print action

- **Goal:** User can download or print.
- **Modules:** FE action (`GuidebookExportActions`)
- **Types:** —
- **Functions:** download handler
- **Services:** none (FE-only)
- **Routes / APIs:** FE-only print/download (server `GET .../pdf` deferred)
- **Algorithms / data:** —
- **Depends on:** P5b.1 or P5b.2
- **Proof:** download/print matches saved structured trip
- **Non-goals:** email delivery

### P5b.4 — No LLM on PDF path

- **Goal:** Assert PDF/print pipeline does not call `LlmGateway`.
- **Modules:** tests
- **Types:** —
- **Functions:** test spy on gateway
- **Services:** —
- **Routes / APIs:** —
- **Algorithms / data:** —
- **Depends on:** P5b.3
- **Proof:** test: render from DTO with fake LLM that fails if called
- **Non-goals:** regenerating narrative

## Proof

Download/print matches saved structured trip

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
