from __future__ import annotations

from typing import Any

import httpx

from src.modules.geo.types import GeoCandidate
from src.ports import GeoGateway


def _classify_place(item: dict[str, Any]) -> tuple[str, int | None]:
    """Map Nominatim class/type/address to place_class + admin_level heuristic."""
    osm_class = str(item.get("class") or "")
    osm_type = str(item.get("type") or "")
    address = item.get("address") or {}
    named_admin = address.get("state") or address.get("region")

    if osm_type == "country" or (
        osm_class == "boundary" and osm_type == "administrative"
    ):
        # Prefer address clues
        if address.get("city") or address.get("town") or address.get("village"):
            if not address.get("country") or item.get("addresstype") in {
                "city",
                "town",
                "village",
                "municipality",
            }:
                return "city", 8
        if item.get("addresstype") == "country" or osm_type == "country":
            return "country", 2
        if item.get("addresstype") in {"state", "region", "province"} or named_admin:
            if item.get("addresstype") in {"state", "region", "province"}:
                return "region", 4

    addresstype = str(item.get("addresstype") or "")
    if addresstype in {"city", "town", "village", "municipality", "suburb"}:
        return "city", 8
    if addresstype in {"state", "region", "province", "county"}:
        return "region", 4
    if addresstype == "country":
        return "country", 2

    if osm_type in {"city", "town", "village", "municipality"}:
        return "city", 8
    if osm_type in {"state", "region", "province", "county"}:
        return "region", 4
    if osm_type == "country":
        return "country", 2

    # bbox span heuristic when metadata is thin
    bbox = _parse_bbox(item.get("boundingbox"))
    if bbox is not None:
        lon_span = abs(bbox[2] - bbox[0])
        lat_span = abs(bbox[3] - bbox[1])
        span = max(lon_span, lat_span)
        if span > 8:
            return "country", 2
        if span > 1.5:
            return "region", 4
        if span > 0:
            return "city", 8

    return "other", None


def _parse_bbox(raw: Any) -> list[float] | None:
    if not raw or len(raw) != 4:
        return None
    try:
        # Nominatim: [south, north, west, east]
        south, north, west, east = (float(x) for x in raw)
        return [west, south, east, north]
    except (TypeError, ValueError):
        return None


class NominatimAdapter(GeoGateway):
    """Nominatim-class geocoder — candidates only; timeout/error → empty list."""

    def __init__(
        self,
        *,
        base_url: str = "https://nominatim.openstreetmap.org",
        user_agent: str = "agentic-trip/0.1 (local; contact: dev@localhost)",
        timeout_seconds: float = 5.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._user_agent = user_agent
        self._timeout = timeout_seconds
        self._client = client

    def search(self, query: str) -> list[GeoCandidate]:
        q = (query or "").strip()
        if not q:
            return []

        params = {
            "q": q,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": 8,
        }
        headers = {"User-Agent": self._user_agent}

        try:
            if self._client is not None:
                response = self._client.get(
                    f"{self._base_url}/search",
                    params=params,
                    headers=headers,
                    timeout=self._timeout,
                )
            else:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.get(
                        f"{self._base_url}/search",
                        params=params,
                        headers=headers,
                    )
            response.raise_for_status()
            payload = response.json()
        except (httpx.TimeoutException, httpx.HTTPError, ValueError, TypeError):
            return []

        if not isinstance(payload, list):
            return []

        candidates: list[GeoCandidate] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            try:
                place_class, admin_level = _classify_place(item)
                osm_type = item.get("osm_type") or "place"
                osm_id = item.get("osm_id") or item.get("place_id")
                geo_id = f"{osm_type}:{osm_id}"
                name = str(
                    item.get("name")
                    or (item.get("address") or {}).get("city")
                    or item.get("display_name")
                    or q
                )
                candidates.append(
                    GeoCandidate(
                        geo_id=geo_id,
                        name=name.split(",")[0].strip(),
                        display_name=str(item.get("display_name") or name),
                        lat=float(item["lat"]),
                        lon=float(item["lon"]),
                        place_class=place_class,
                        admin_level=admin_level,
                        bbox=_parse_bbox(item.get("boundingbox")),
                        country_code=(item.get("address") or {}).get("country_code"),
                        extra={
                            "addresstype": item.get("addresstype"),
                            "class": item.get("class"),
                            "type": item.get("type"),
                        },
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return candidates
