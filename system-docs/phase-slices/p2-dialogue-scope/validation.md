# P2 Dialogue + TripScope + HITL — validation gate

A slice is **done** only when every sub-phase proof below and the phase-level checks pass. Then proceed to the next phase-slice.

## Sub-phase checks

| ID | Proof |
|----|--------|
| P2.1 | [ ] parse_intent structured / ask on missing duration; `LiteLlmAdapter` when keys exist, stub when missing |
| P2.2 | [ ] GeoGateway mock timeout → empty |
| P2.3 | [ ] 0/1/N candidates |
| P2.4 | [ ] classify_scope unit cases incl. country-long `hubs[]` or HITL |
| P2.5 | [ ] Paris interrupt |
| P2.6 | [ ] HITL resume API |
| P2.7 | [ ] trip_scope written |
| P2.8 | [ ] FE chips (manual note OK) |
| P2.9 | [ ] Scope goldens: city; Tuscany-style region; country-short; Kyoto-wins; Japan-10-days-or-HITL; Paris; missing duration |

## Checks

- [ ] Golden scope classification cases (bible: city / region / country-short / named-city-wins / country-long / ambiguous / missing duration)
- [ ] HITL interrupt resume with choice
- [ ] geo gateway fail-soft tests

## CI

- [ ] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [ ] Failures block merging/applying the next slice

## Exit criteria

- All sub-phase proofs satisfied
- Phase-level proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p2-dialogue-scope` tasks complete (when that change exists)
