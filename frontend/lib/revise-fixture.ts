import type { GuidebookExport } from "@/lib/sse";

/** Multi-stop day 2 so “less walking” can drop stops without a live API. */
export const REVISE_FIXTURE_BEFORE: GuidebookExport = {
  trip_id: "revise-fixture-1",
  cover: {
    title: "Kyoto draft",
    status: "draft",
    day_count: 2,
    stop_count: 6,
    hubs: [],
  },
  hubs: [],
  days: [
    {
      day_index: 1,
      title: "Arrive",
      stops: [
        { place_id: "place-fushimi", name: "Fushimi Inari", lon: 135.77, lat: 34.97 },
        { place_id: "place-kiyomizu", name: "Kiyomizu", lon: 135.78, lat: 34.99 },
      ],
    },
    {
      day_index: 2,
      title: "Walk day",
      stops: [
        { place_id: "place-gion", name: "Gion", lon: 135.77, lat: 35.0 },
        { place_id: "place-arashiyama", name: "Arashiyama", lon: 135.67, lat: 35.01 },
        { place_id: "place-bamboo", name: "Bamboo Grove", lon: 135.67, lat: 35.02 },
        { place_id: "place-kinkaku", name: "Kinkakuji", lon: 135.73, lat: 35.04 },
      ],
    },
  ],
  narratives: [],
  map_points: [
    { place_id: "place-fushimi", name: "Fushimi Inari", lon: 135.77, lat: 34.97, day_index: 1 },
    { place_id: "place-kiyomizu", name: "Kiyomizu", lon: 135.78, lat: 34.99, day_index: 1 },
    { place_id: "place-gion", name: "Gion", lon: 135.77, lat: 35.0, day_index: 2 },
    { place_id: "place-arashiyama", name: "Arashiyama", lon: 135.67, lat: 35.01, day_index: 2 },
    { place_id: "place-bamboo", name: "Bamboo Grove", lon: 135.67, lat: 35.02, day_index: 2 },
    { place_id: "place-kinkaku", name: "Kinkakuji", lon: 135.73, lat: 35.04, day_index: 2 },
  ],
};

export const REVISE_FIXTURE_AFTER: GuidebookExport = {
  ...REVISE_FIXTURE_BEFORE,
  cover: {
    ...REVISE_FIXTURE_BEFORE.cover,
    stop_count: 4,
  },
  days: [
    REVISE_FIXTURE_BEFORE.days![0],
    {
      day_index: 2,
      title: "Walk day",
      stops: [
        { place_id: "place-gion", name: "Gion", lon: 135.77, lat: 35.0 },
        { place_id: "place-kinkaku", name: "Kinkakuji", lon: 135.73, lat: 35.04 },
      ],
    },
  ],
  map_points: [
    { place_id: "place-fushimi", name: "Fushimi Inari", lon: 135.77, lat: 34.97, day_index: 1 },
    { place_id: "place-kiyomizu", name: "Kiyomizu", lon: 135.78, lat: 34.99, day_index: 1 },
    { place_id: "place-gion", name: "Gion", lon: 135.77, lat: 35.0, day_index: 2 },
    { place_id: "place-kinkaku", name: "Kinkakuji", lon: 135.73, lat: 35.04, day_index: 2 },
  ],
};
