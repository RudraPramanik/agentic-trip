# Frontend Build plan CTA — manual proof (P4.11 / task 10.2)

## Expected behavior

1. Confirm `trip_scope` via chat/HITL → **Build plan** appears.
2. Scope confirm / chat send / catalog acquire do **not** start generate.
3. Click **Build plan** → SSE progress stages → draft summary on session.
4. Optional **Abort** during generate → aborted outcome; no successful draft from that run.

## Quick check

- With API + FE running: lock a city scope → Build plan visible → click → status shows stages → draft day/stop counts appear.
- Send another chat message without clicking Build plan → generate does not start.
