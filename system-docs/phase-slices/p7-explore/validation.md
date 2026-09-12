# P7 Explore — validation gate

A slice is **done** only when every sub-phase proof below and the phase-level checks pass. Then proceed to the next phase-slice.

## Sub-phase checks

| ID | Proof |
|----|--------|
| P7.1 | [ ] GPS then IP; honest empty |
| P7.2 | [ ] last-trip locked on guest draft; fixture saved → ids or empty |
| P7.3 | [ ] explore HTTP ASGI |
| P7.4 | [ ] FE dual-tab: anchors persist; IP approximate copy; plan-from-card real identity |
| P7.5 | [ ] no fake POI ids; last-trip locked on draft |

## Checks

- [ ] last-trip locked on draft (not unlocked by guest generate)
- [ ] IP approximate labeling
- [ ] tab switch does not destroy the other anchor
- [ ] no fake POI ids

## CI

- [ ] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [ ] Failures block merging/applying the next slice

## Exit criteria

- All sub-phase proofs satisfied
- Phase-level proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p7-explore` tasks complete (when that change exists)
