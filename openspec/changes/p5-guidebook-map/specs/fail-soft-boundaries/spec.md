## ADDED Requirements

### Requirement: Map style and media fail soft without fake visuals

Supported external dependency kinds MUST also include map basemap/style load and place media resolution. Map style failure MUST fall back to list-first guidebook content. Missing or failed media MUST use an honest category/gradient (or equivalent) fallback and MUST NOT present invented images as photographs of that venue. Place media resolution MUST NOT run on the generate hot path.

#### Scenario: Map style fail keeps list usable

- **WHEN** the map basemap or style URL fails to load while viewing a trip
- **THEN** the day/stop list remains usable and the UI does not invent map geometry to compensate

#### Scenario: Missing media is honest

- **WHEN** place media is unavailable for a stop
- **THEN** the UI uses an honest non-photo fallback and does not claim a real venue photograph

#### Scenario: Media not on generate path

- **WHEN** generate is running
- **THEN** the system does not call place media providers as part of generate stages
