## MODIFIED Requirements

### Requirement: Placeholder stays slot is allowed

The trip guidebook UI MUST show an empty stays/booking block (or “coming later” equivalent) adjacent to the itinerary for reopenable draft trips after generate. The block MUST NOT invent live prices or availability. Copy MUST NOT claim a reservation exists. Booking product HTTP and vendor SDKs remain deferred to the booking slice; v1 UI hollow state does not require those APIs.

#### Scenario: Empty stays on a saved trip

- **WHEN** a saved trip is opened and no booking vendor is configured
- **THEN** the stays area is empty or explicitly unavailable, with no fake rates

#### Scenario: Empty stays on a reopenable draft trip

- **WHEN** a draft trip guidebook is opened and no booking vendor is configured
- **THEN** the stays area is empty or explicitly unavailable, with no fake rates

#### Scenario: Empty stays does not block trip view

- **WHEN** the guest views guidebook days and map with an empty booking block
- **THEN** the itinerary and map remain usable without completing any booking
