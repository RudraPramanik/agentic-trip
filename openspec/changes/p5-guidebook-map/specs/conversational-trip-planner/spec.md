## MODIFIED Requirements

### Requirement: Saved trip is a structured artifact with a map

After a successful generate, the system MUST persist a trip the user can reopen as a draft (v1) with guidebook UI and map. The artifact MUST include ordered days and stops grounded in real places (stable place identity and coordinates from geo/catalog tools, not free-form LLM invention). The guidebook MUST render those days from the structured trip / GuidebookExport (not a second LLM narrative pipeline). The map MUST show those stops; road polylines MUST appear when routing geometry exists, otherwise points only. v1 MUST ship points-only unless a later slice stores route geometry on the trip. The system MUST NOT invent coordinates to draw a prettier line.

#### Scenario: Itinerary is reopenable

- **WHEN** generate completes successfully
- **THEN** the user can open the trip later and see the same day list and mapped stops

#### Scenario: Itinerary is reopenable as guidebook

- **WHEN** generate completes successfully
- **THEN** the user can open the trip guidebook later and see the same day list and mapped stops

#### Scenario: No hallucinated map geometry

- **WHEN** routing geometry is missing for a leg
- **THEN** the map still shows stop points and does not fabricate a polyline

#### Scenario: Guidebook and export share one structure

- **WHEN** the user views the guidebook or fetches export JSON for the same trip
- **THEN** days, stops, and coordinates come from the same structured trip mapping without an LLM rewrite of structure
