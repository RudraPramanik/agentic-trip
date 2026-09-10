## Purpose

Defines location-based Explore for the conversational trip OS: a near-me feed from GPS with IP fallback, and a last-trip-location feed that exists only after a trip is saved. Chat geo-resolve MUST NOT populate Explore before save.

## ADDED Requirements

### Requirement: Dual-tab location explore

Explore MUST offer two subtabs the user can switch: **Near me** and **Last trip location** (wording MAY vary). Switching tabs MUST NOT destroy the other tab’s anchor. The feed MUST be place cards (Instagram-like masonry is allowed) grounded in real catalog places. The system MUST NOT invent venues or coordinates for the feed.

#### Scenario: User switches tabs

- **WHEN** the user is on Near me and switches to Last trip location (or back)
- **THEN** both anchors remain independently valid; switching does not require re-prompting GPS solely because the other tab was selected

### Requirement: Near me uses GPS then IP

Near me MUST prefer device geolocation when the user grants permission. If GPS is denied, unavailable, or times out, the system MUST fall back to an IP-based approximate location for the feed. If both fail, Explore MUST show an empty/permission state and MUST NOT fake a city.

#### Scenario: GPS granted

- **WHEN** the user opens Near me and grants location permission with a usable fix
- **THEN** the feed is nearby places for that fix (radius/bbox grounded in geo tools)

#### Scenario: GPS denied uses IP

- **WHEN** the user denies or cannot provide GPS
- **THEN** the feed uses IP-approximate location when that lookup succeeds

#### Scenario: No location at all

- **WHEN** GPS is unavailable and IP lookup fails
- **THEN** Near me shows an honest empty or error state with a way to retry, not a fabricated destination catalog

### Requirement: Last trip location only after a saved trip

The Last trip location tab MUST populate from the geography of a **persisted trip** (the trip’s resolved scope / planning location). The system MUST NOT set this tab from a chat geo-resolve, HITL pick, or unsaved draft. If the user has no saved trip, that tab MUST be empty with copy that a saved plan unlocks it.

#### Scenario: No saved trip yet

- **WHEN** a visitor has chatted (even if geo was resolved in conversation) but has not saved a trip
- **THEN** Last trip location is empty / locked and does not show POIs for the chat-resolved place

#### Scenario: After save

- **WHEN** a trip has been saved successfully
- **THEN** Last trip location can show a place feed for that trip’s location/scope, and Near me remains GPS/IP-based and independent

#### Scenario: Newer saved trip wins

- **WHEN** the user saves a later trip with a different scope
- **THEN** Last trip location follows the most recently saved trip location unless the user explicitly pins another saved trip (pinning is optional; default is latest saved)

### Requirement: Honest media and no social graph in v1

Explore cards MUST NOT claim category art or stock media are photographs of the venue unless a real place-media URL exists. Likes, follows, and stories are out of scope. A card MAY offer a way to start or continue planning for that real place; it MUST NOT call trip day-edit APIs as if the card were already on an itinerary.

#### Scenario: Card without venue photo

- **WHEN** a feed place has no verified photo
- **THEN** the card still renders with non-photo fallback and does not present the fallback as a photo of that venue

#### Scenario: Plan from a card

- **WHEN** the user acts on a live place card to plan
- **THEN** planning uses that place’s real identity; no fake ids
