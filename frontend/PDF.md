# P5b PDF / print export — local notes

## Env vars needed (names only)

Copy from `.env.demo` into local `.env` (never commit `.env`):

- `DATABASE_URL`
- `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`
- `LLM_MODEL`, `LLM_API_KEY`, `LLM_API_BASE` (NVIDIA NIM primary)
- `LLM_MODEL_FALLBACKS` (include Gemini)
- `GEMINI_API_KEY`, `EMBEDDING_MODEL`
- Frontend: `NEXT_PUBLIC_API_BASE` (optional; defaults `http://localhost:8000`)

## Proofs

- **Unit:** `npm test` — fixture projection, incomplete export fail-soft, PDF blob without LLM call, no invented rates.
- **Playwright:** `npm run test:e2e` — `/guidebook-fixture` Print + Download PDF.
- **Backend:** `uv run pytest tests/test_trips_pdf.py tests/test_trips_api.py` — no `GET .../pdf`; export ownership intact.

## Product path

FE print CSS + `@react-pdf/renderer` from `GuidebookExport` via `GET /api/v1/trips/{id}/export`. Server PDF deferred.
