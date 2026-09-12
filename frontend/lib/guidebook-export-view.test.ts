import { describe, expect, it, vi } from "vitest";

import {
  containsInventedBookingRates,
  projectGuidebookExport,
  projectionPlainText,
  requireCompleteExport,
} from "@/lib/guidebook-export-view";
import { FIXTURE_GUIDEBOOK_EXPORT } from "@/lib/guidebook-fixture";
import type { GuidebookExport } from "@/lib/sse";

describe("projectGuidebookExport", () => {
  it("maps fixture days/stops without inventing place ids", () => {
    const p = projectGuidebookExport(FIXTURE_GUIDEBOOK_EXPORT);
    expect(p.title).toBe("Fixture Coastal Escape");
    expect(p.days).toHaveLength(2);
    expect(p.days[0].stops.map((s) => s.place_id)).toEqual([
      "place-bridge",
      "place-market",
    ]);
    expect(p.days[1].stops.map((s) => s.place_id)).toEqual(["place-lighthouse"]);
    expect(p.days[0].stops.map((s) => s.label)).toEqual([
      "Old Bridge",
      "Fish Market",
    ]);
    const text = projectionPlainText(p);
    expect(text).toContain("Old Bridge");
    expect(text).toContain("place-lighthouse");
    expect(text).not.toContain("Invented Hotel");
    expect(containsInventedBookingRates(text)).toBe(false);
  });
});

describe("requireCompleteExport", () => {
  it("fails honestly on missing days", () => {
    const bad: GuidebookExport = { trip_id: "x", days: [] };
    const r = requireCompleteExport(bad);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/no days/i);
  });

  it("fails on stop without place_id", () => {
    const bad: GuidebookExport = {
      days: [{ day_index: 1, stops: [{ name: "Ghost" }] }],
    };
    const r = requireCompleteExport(bad);
    expect(r.ok).toBe(false);
  });

  it("accepts fixture", () => {
    const r = requireCompleteExport(FIXTURE_GUIDEBOOK_EXPORT);
    expect(r.ok).toBe(true);
  });
});

describe("PDF path never calls LLM", () => {
  it("renderGuidebookPdf does not invoke a fake LLM gateway", async () => {
    const llmSpy = vi.fn(() => {
      throw new Error("LlmGateway must not be called on PDF path");
    });
    (globalThis as { __fakeLlmGateway?: () => void }).__fakeLlmGateway = llmSpy;

    const { renderGuidebookPdf } = await import("@/components/guidebook-pdf");
    const blob = await renderGuidebookPdf(FIXTURE_GUIDEBOOK_EXPORT);
    expect(blob.type).toContain("pdf");
    expect(blob.size).toBeGreaterThan(100);
    expect(llmSpy).not.toHaveBeenCalled();

    // Content proof via projection text (same fields fed to PDF)
    const text = projectionPlainText(
      projectGuidebookExport(FIXTURE_GUIDEBOOK_EXPORT),
    );
    expect(text).toContain("Fish Market");
    expect(text).not.toContain("Extra Venue");
    expect(containsInventedBookingRates(text)).toBe(false);

    delete (globalThis as { __fakeLlmGateway?: () => void }).__fakeLlmGateway;
  });
});
