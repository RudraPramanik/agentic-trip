import type { GuidebookExport } from "@/lib/sse";

/** Pure projection of GuidebookExport for print/PDF — never invents fields. */
export type GuidebookStopSection = {
  place_id: string;
  label: string;
};

export type GuidebookDaySection = {
  day_index: number;
  title: string | null;
  story: string | null;
  stops: GuidebookStopSection[];
};

export type GuidebookExportProjection = {
  trip_id: string | null;
  title: string;
  status: string;
  day_count: number;
  stop_count: number;
  hubs: string[];
  days: GuidebookDaySection[];
  narratives: { day_index: number; title: string | null; story: string | null }[];
};

export type ExportCompleteness =
  | { ok: true; projection: GuidebookExportProjection }
  | { ok: false; error: string };

function stopLabel(stop: {
  place_id?: string;
  name?: string;
  title?: string | null;
}): string {
  return stop.title || stop.name || stop.place_id || "";
}

/** Map export JSON → print/PDF sections. Does not invent venues, rates, or coords. */
export function projectGuidebookExport(
  exportData: GuidebookExport,
): GuidebookExportProjection {
  const days = (exportData.days ?? []).map((day) => ({
    day_index: day.day_index ?? 0,
    title: day.title ?? null,
    story: day.story ?? null,
    stops: (day.stops ?? []).map((stop) => ({
      place_id: stop.place_id ?? "",
      label: stopLabel(stop),
    })),
  }));

  const stop_count =
    exportData.cover?.stop_count ??
    days.reduce((n, d) => n + d.stops.length, 0);

  return {
    trip_id: exportData.trip_id ?? null,
    title: exportData.cover?.title ?? "Trip draft",
    status: exportData.cover?.status ?? "draft",
    day_count: exportData.cover?.day_count ?? days.length,
    stop_count,
    hubs: exportData.hubs ?? exportData.cover?.hubs ?? [],
    days,
    narratives: (exportData.narratives ?? []).map((n) => ({
      day_index: n.day_index ?? 0,
      title: n.title ?? null,
      story: n.story ?? null,
    })),
  };
}

/** Fail soft: incomplete export must not be filled with invented content. */
export function requireCompleteExport(
  exportData: GuidebookExport | null | undefined,
): ExportCompleteness {
  if (!exportData) {
    return { ok: false, error: "Export is missing — cannot print or download." };
  }
  if (!Array.isArray(exportData.days) || exportData.days.length === 0) {
    return {
      ok: false,
      error: "Export has no days — cannot invent itinerary content.",
    };
  }
  for (const day of exportData.days) {
    const stops = day.stops ?? [];
    for (const stop of stops) {
      if (!stop.place_id) {
        return {
          ok: false,
          error: "Export has a stop without place_id — refusing to invent identity.",
        };
      }
    }
  }
  return { ok: true, projection: projectGuidebookExport(exportData) };
}

/** Flatten projection to plain text for tests / PDF content proofs. */
export function projectionPlainText(p: GuidebookExportProjection): string {
  const lines: string[] = [
    p.title,
    `${p.status} · ${p.day_count} days · ${p.stop_count} stops`,
  ];
  if (p.hubs.length) lines.push(`Hubs: ${p.hubs.join(" → ")}`);
  for (const day of p.days) {
    lines.push(
      `Day ${day.day_index}${day.title ? `: ${day.title}` : ""}`,
    );
    if (day.story) lines.push(day.story);
    for (const stop of day.stops) {
      lines.push(`- ${stop.label} (${stop.place_id})`);
    }
  }
  lines.push("Stays, flights & activities");
  lines.push("Coming later — no rates or reservations yet.");
  return lines.join("\n");
}

/** Detect invented booking-rate patterns (hollow booking posture). */
export function containsInventedBookingRates(text: string): boolean {
  return /\$\d|\d+\s*(USD|EUR|GBP)|per\s*night|from\s*\$/i.test(text);
}
