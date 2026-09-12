"use client";

import type { ReactNode } from "react";

import type { GuidebookExport } from "@/lib/sse";

/** Hollow booking slot — no rates, no vendor SDKs (P5.5 / P8 owns API). */
export function BookingPlaceholder() {
  return (
    <section className="booking-placeholder" aria-label="Booking placeholder">
      <h3>Stays, flights & activities</h3>
      <p className="booking-empty">Coming later — no rates or reservations yet.</p>
      <ul className="booking-slots">
        <li>Stays: empty</li>
        <li>Flights: empty</li>
        <li>Activities: empty</li>
      </ul>
    </section>
  );
}

type Props = {
  exportData: GuidebookExport;
  mapSlot?: ReactNode;
};

export function GuidebookView({ exportData, mapSlot }: Props) {
  const cover = exportData.cover;
  const days = exportData.days ?? [];
  return (
    <article className="guidebook" aria-label="Trip guidebook">
      <header className="guidebook-cover">
        <h2>{cover?.title ?? "Trip draft"}</h2>
        <p className="guidebook-meta">
          {cover?.status ?? "draft"} · {cover?.day_count ?? days.length} days ·{" "}
          {cover?.stop_count ?? 0} stops
        </p>
        {(exportData.hubs?.length ?? 0) > 0 ? (
          <p className="guidebook-hubs">Hubs: {exportData.hubs?.join(" → ")}</p>
        ) : null}
      </header>
      {mapSlot}
      {days.map((day) => (
        <section
          key={day.day_index}
          className="guidebook-day"
          aria-label={`Day ${day.day_index}`}
        >
          <h3>
            Day {day.day_index}
            {day.title ? `: ${day.title}` : ""}
          </h3>
          {day.story ? <p className="guidebook-story">{day.story}</p> : null}
          <ul className="guidebook-stops">
            {(day.stops ?? []).map((stop) => (
              <li key={`${day.day_index}-${stop.place_id}`}>
                {stop.title || stop.name || stop.place_id}
              </li>
            ))}
          </ul>
        </section>
      ))}
      <BookingPlaceholder />
    </article>
  );
}
