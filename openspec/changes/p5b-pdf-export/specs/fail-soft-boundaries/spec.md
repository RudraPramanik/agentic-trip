## ADDED Requirements

### Requirement: PDF and print path fails soft without inventing content

PDF and print rendering MUST treat incomplete GuidebookExport as a hard fail with a clear user-visible error. Render failures MUST leave the stored trip intact. The PDF/print path MUST NOT call the language-model gateway, MUST NOT invent hotels, prices, venues, or coordinates, and MUST NOT fabricate booking rates to fill the document.

#### Scenario: Incomplete export does not invent fill

- **WHEN** GuidebookExport is missing required days/stops for print or PDF
- **THEN** the system fails with a clear error and does not invent hotels, prices, or stops

#### Scenario: Render failure preserves trip

- **WHEN** print or PDF rendering fails after a valid export was loaded
- **THEN** the user sees an error and the trip artifact remains unchanged and reopenable

#### Scenario: No language model on PDF path

- **WHEN** print or PDF rendering runs
- **THEN** the language-model gateway is not called for that path
