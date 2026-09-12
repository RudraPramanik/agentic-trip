"use client";

import type { GuidebookExportProjection } from "@/lib/guidebook-export-view";

type Props = {
  projection: GuidebookExportProjection;
};

/** Print-only layout; screen chrome is hidden via @media print on siblings. */
export function GuidebookPrintView({ projection }: Props) {
  return (
    <article
      className="guidebook-print"
      aria-label="Printable guidebook"
      data-testid="guidebook-print"
    >
      <header className="guidebook-print-cover">
        <h1>{projection.title}</h1>
        <p>
          {projection.status} · {projection.day_count} days ·{" "}
          {projection.stop_count} stops
        </p>
        {projection.hubs.length > 0 ? (
          <p>Hubs: {projection.hubs.join(" → ")}</p>
        ) : null}
      </header>
      {projection.days.map((day) => (
        <section
          key={day.day_index}
          className="guidebook-print-day"
          data-day-index={day.day_index}
        >
          <h2>
            Day {day.day_index}
            {day.title ? `: ${day.title}` : ""}
          </h2>
          {day.story ? <p>{day.story}</p> : null}
          <ul>
            {day.stops.map((stop) => (
              <li key={`${day.day_index}-${stop.place_id}`} data-place-id={stop.place_id}>
                {stop.label}
              </li>
            ))}
          </ul>
        </section>
      ))}
      <section className="guidebook-print-booking" aria-label="Booking placeholder">
        <h2>Stays, flights & activities</h2>
        <p>Coming later — no rates or reservations yet.</p>
      </section>
    </article>
  );
}
