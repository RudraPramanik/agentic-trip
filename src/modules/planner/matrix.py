"""Travel-time helpers — OSRM table if present else haversine + penalty; no fake geometry."""

from __future__ import annotations

import math
from typing import Any, Protocol


class TravelTable(Protocol):
    """Optional routing table (e.g. OSRM). Must return seconds between place indices."""

    def durations_seconds(self, places: list[dict[str, Any]]) -> list[list[float]] | None:
        """Return NxN duration matrix in seconds, or None to fall soft."""
        ...


# Walking / transfer soft penalty: treat crow-flies as ~4 km/h + fixed overhead.
_HAVERSINE_SPEED_M_PER_S = 4000.0 / 3600.0  # ~1.11 m/s
_HAVERSINE_FIXED_PENALTY_S = 300.0  # 5 minutes


def haversine_meters(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Spherical distance in meters between (lon, lat) pairs."""
    lon1, lat1 = a
    lon2, lat2 = b
    r = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    h = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    )
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def _coords(place: dict[str, Any]) -> tuple[float, float] | None:
    lon = place.get("lon")
    lat = place.get("lat")
    if lon is None or lat is None:
        return None
    return float(lon), float(lat)


def travel_matrix(
    places: list[dict[str, Any]],
    *,
    table: TravelTable | None = None,
) -> dict[str, Any]:
    """Build pairwise travel times. Never invents polyline / LineString geometry.

    Returns:
      {
        "durations_seconds": list[list[float]],  # NxN finite floats
        "source": "osrm" | "haversine",
        "geometry": None,  # explicitly never fabricated
      }
    """
    n = len(places)
    if table is not None:
        try:
            durations = table.durations_seconds(places)
        except Exception:
            durations = None
        if durations is not None and len(durations) == n:
            # Ensure finite floats; fall soft if malformed
            try:
                matrix = [[float(durations[i][j]) for j in range(n)] for i in range(n)]
                if all(math.isfinite(matrix[i][j]) for i in range(n) for j in range(n)):
                    return {
                        "durations_seconds": matrix,
                        "source": "osrm",
                        "geometry": None,
                    }
            except (TypeError, ValueError, IndexError):
                pass

    matrix: list[list[float]] = [[0.0] * n for _ in range(n)]
    coords = [_coords(p) for p in places]
    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 0.0
                continue
            ci, cj = coords[i], coords[j]
            if ci is None or cj is None:
                matrix[i][j] = _HAVERSINE_FIXED_PENALTY_S * 2
                continue
            dist = haversine_meters(ci, cj)
            matrix[i][j] = dist / _HAVERSINE_SPEED_M_PER_S + _HAVERSINE_FIXED_PENALTY_S
    return {
        "durations_seconds": matrix,
        "source": "haversine",
        "geometry": None,
    }
