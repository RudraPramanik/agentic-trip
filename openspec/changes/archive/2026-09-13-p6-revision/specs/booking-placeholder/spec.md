## ADDED Requirements

### Requirement: Revise keeps hollow booking posture

A structural replan MUST NOT invent live prices, availability, or reservation claims, and MUST NOT mutate the hollow booking slot into a booked or priced state. Booking remains a later trip-keyed concern after authenticated save.

#### Scenario: Successful revise does not invent rates

- **WHEN** revise completes successfully and the guest reopens the draft trip or guidebook
- **THEN** the stays/booking area remains empty or explicitly unavailable, with no fake rates
