"use client";

import { useEffect, useRef, useState } from "react";

import type { GuidebookExport } from "@/lib/sse";

const FALLBACK_STYLE =
  process.env.NEXT_PUBLIC_MAP_STYLE_URL ??
  "https://demotiles.maplibre.org/style.json";

type Props = {
  exportData: GuidebookExport;
  onStyleFail?: () => void;
};

/**
 * MapLibre trip map: points always; polyline only if route_geometry exists.
 * Never invents crow-flies as roads. List-first when style fails.
 */
export function TripMap({ exportData, onStyleFail }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [failed, setFailed] = useState(false);
  const points = exportData.map_points ?? [];
  const hasGeom =
    Array.isArray(exportData.route_geometry) &&
    exportData.route_geometry.length > 0;

  useEffect(() => {
    if (!containerRef.current || points.length === 0) return;
    let cancelled = false;
    let map: import("maplibre-gl").Map | null = null;

    (async () => {
      try {
        const maplibregl = await import("maplibre-gl");
        await import("maplibre-gl/dist/maplibre-gl.css");
        if (cancelled || !containerRef.current) return;

        map = new maplibregl.Map({
          container: containerRef.current,
          style: FALLBACK_STYLE,
          center: [points[0].lon ?? 0, points[0].lat ?? 0],
          zoom: 8,
        });

        map.on("error", () => {
          setFailed(true);
          onStyleFail?.();
        });

        map.on("load", () => {
          if (!map) return;
          const features = points
            .filter((p) => p.lon != null && p.lat != null)
            .map((p) => ({
              type: "Feature" as const,
              properties: { name: p.name ?? p.place_id },
              geometry: {
                type: "Point" as const,
                coordinates: [p.lon as number, p.lat as number],
              },
            }));

          map.addSource("stops", {
            type: "geojson",
            data: { type: "FeatureCollection", features },
          });
          map.addLayer({
            id: "stops-circle",
            type: "circle",
            source: "stops",
            paint: {
              "circle-radius": 6,
              "circle-color": "#0f6b4c",
              "circle-stroke-width": 1,
              "circle-stroke-color": "#fff",
            },
          });

          // Polyline only when geometry already exists — never invent crow-flies.
          if (hasGeom && exportData.route_geometry) {
            map.addSource("route", {
              type: "geojson",
              data: {
                type: "Feature",
                properties: {},
                geometry: {
                  type: "LineString",
                  coordinates: exportData.route_geometry as number[][],
                },
              },
            });
            map.addLayer({
              id: "route-line",
              type: "line",
              source: "route",
              paint: { "line-color": "#0f6b4c", "line-width": 3 },
            });
          }

          if (features.length > 1) {
            const bounds = new maplibregl.LngLatBounds(
              features[0].geometry.coordinates as [number, number],
              features[0].geometry.coordinates as [number, number],
            );
            for (const f of features) {
              bounds.extend(f.geometry.coordinates as [number, number]);
            }
            map.fitBounds(bounds, { padding: 40, maxZoom: 12 });
          }
        });
      } catch {
        setFailed(true);
        onStyleFail?.();
      }
    })();

    return () => {
      cancelled = true;
      map?.remove();
    };
  }, [points, hasGeom, exportData.route_geometry, onStyleFail]);

  if (points.length === 0) {
    return (
      <p className="map-empty" role="status">
        No mapped stops (missing coordinates).
      </p>
    );
  }

  if (failed) {
    return (
      <p className="map-fallback" role="status">
        Map unavailable — showing list only (no invented routes).
      </p>
    );
  }

  return (
    <div
      className="trip-map"
      ref={containerRef}
      role="img"
      aria-label="Trip stop map"
      data-testid="trip-map"
      data-stop-ids={points.map((p) => p.place_id).join(",")}
      data-points-only={hasGeom ? "false" : "true"}
    />
  );
}
