"use client";

import { GuidebookView } from "@/components/guidebook-view";
import { FIXTURE_GUIDEBOOK_EXPORT } from "@/lib/guidebook-fixture";

/** Static fixture page for Playwright / local print-PDF smoke (no generate required). */
export default function GuidebookFixturePage() {
  return (
    <main className="shell">
      <header className="no-print">
        <h1>Guidebook fixture</h1>
        <p className="status">P5b print/PDF smoke — fixture export only</p>
      </header>
      <GuidebookView exportData={FIXTURE_GUIDEBOOK_EXPORT} />
    </main>
  );
}
