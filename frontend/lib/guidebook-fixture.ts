import type { GuidebookExport } from "@/lib/sse";

/** Stable fixture for unit/Playwright proofs — days/stops only, no rates. */
export const FIXTURE_GUIDEBOOK_EXPORT: GuidebookExport = {
  trip_id: "fixture-trip-1",
  cover: {
    title: "Fixture Coastal Escape",
    status: "draft",
    day_count: 2,
    stop_count: 3,
    hubs: ["Harbor", "Cliff"],
  },
  hubs: ["Harbor", "Cliff"],
  days: [
    {
      day_index: 1,
      title: "Arrive",
      story: "Ease into the harbor.",
      stops: [
        { place_id: "place-bridge", name: "Old Bridge", lon: 91.1, lat: 25.2 },
        { place_id: "place-market", name: "Fish Market", lon: 91.12, lat: 25.21 },
      ],
    },
    {
      day_index: 2,
      title: "Cliffs",
      story: "Walk the ridge.",
      stops: [
        { place_id: "place-lighthouse", name: "Lighthouse", lon: 91.15, lat: 25.25 },
      ],
    },
  ],
  narratives: [
    { day_index: 1, title: "Arrive", story: "Ease into the harbor." },
    { day_index: 2, title: "Cliffs", story: "Walk the ridge." },
  ],
  map_points: [
    { place_id: "place-bridge", name: "Old Bridge", lon: 91.1, lat: 25.2, day_index: 1 },
    { place_id: "place-market", name: "Fish Market", lon: 91.12, lat: 25.21, day_index: 1 },
    {
      place_id: "place-lighthouse",
      name: "Lighthouse",
      lon: 91.15,
      lat: 25.25,
      day_index: 2,
    },
  ],
};
