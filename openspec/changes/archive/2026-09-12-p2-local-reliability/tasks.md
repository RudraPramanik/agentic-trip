## 1. Boot flag and schema entrypoint

- [x] 1.1 [backend] Add `APPLY_SCHEMA_ON_BOOT` (default false) to settings; do not invent Wandr env names
- [x] 1.2 [backend] Add a boot entry that runs `alembic upgrade head` when the flag is true, then starts uvicorn
- [x] 1.3 [infra] Point Dockerfile CMD at that entry; avoid `uv run` package rebuild on every start (`--no-sync` or venv uvicorn)
- [x] 1.4 [infra] Set `APPLY_SCHEMA_ON_BOOT=true` on Compose `api`
- [x] 1.5 [backend] Proof: with flag true against an empty product DB, boot applies head and process binds; `create_app()` in unit tests does not migrate

## 2. Honest schema failure + LLM composition root

- [x] 2.1 [backend] Map missing session relation on create (and other session SQL writes) to 503 `{"detail":{"code":"schema_unavailable","message":"…"}}` — no invented session
- [x] 2.2 [backend] Wire `create_app()` with `dialogue_stub_fallback=False`; keep `LocalDialogueStub` only as an explicit test double
- [x] 2.3 [backend] Proof: ASGI test create-session without table → 503 problem body; wired gateway complete without keys → structured unavailable, not canned stub text; missing-duration turn still asks and does not persist `trip_scope`

## 3. Docs and validation ticks

- [x] 3.1 [docs] README: Compose `up --build` applies schema; copy `.env.example`; if host alembic/pytest say `role "at" does not exist`, another Postgres owns `5432`
- [x] 3.2 [docs] `.env.example`: document `APPLY_SCHEMA_ON_BOOT` and the existing `DATABASE_URL` (no new product URL names)
- [x] 3.3 [docs] Check off completed P0/P1 proofs in `system-docs/phase-slices/p0-foundation/validation.md` and `p1-chat/validation.md`
- [x] 3.4 [infra] Proof: `uv run pytest` green; documented Compose path can `POST /api/v1/sessions` after `api`+`db` start without a manual host migrate
