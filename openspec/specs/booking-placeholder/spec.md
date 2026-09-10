# booking-placeholder Specification

## Purpose

Defines the deferred booking surface for the conversational trip OS: v1 may show an empty stays slot, and later hotel/options MUST key off a saved trip’s location, not unsaved chat geography.

## Requirements

### Requirement: Booking is not required to complete a trip

The user MUST be able to finish and save a planned itinerary with map days without completing any booking. v1 MUST NOT block save or trip view on a lodging or flight vendor.

#### Scenario: Save without booking

- **WHEN** generate succeeds and the user has not chosen a hotel or flight
- **THEN** the trip still saves and remains viewable with days and map

### Requirement: Placeholder stays slot is allowed

The trip UI MAY show an empty stays/booking block (or “coming later” equivalent) adjacent to the itinerary. The block MUST NOT invent live prices or availability. Copy MUST NOT claim a reservation exists.

#### Scenario: Empty stays on a saved trip

- **WHEN** a saved trip is opened and no booking vendor is configured
- **THEN** the stays area is empty or explicitly unavailable, with no fake rates

### Requirement: Future options key off saved trip location

If and when hotels or similar options are added, they MUST be scoped to the **saved trip** location/region, not to GPS, IP, or an unsaved chat resolve. Until a trip is saved, the product MUST NOT show trip-keyed hotel options as if a plan existed.

#### Scenario: No trip, no trip-keyed hotels

- **WHEN** the user is only chatting or browsing Explore and has no saved trip
- **THEN** the system does not present hotels as belonging to “this trip”

#### Scenario: Options after save

- **WHEN** a trip is saved and a later booking provider is enabled
- **THEN** listed stays/options are for that trip’s resolved location, not for the user’s current IP/GPS unless the user explicitly asks for near-me lodging as a separate action
