from __future__ import annotations

from typing import Any

import httpx

from src.modules.catalog.models import PlaceRecord


class OverpassAdapter:
    """Overpass QL adapter — fail-soft to empty on timeout/error."""

    def __init__(
        self,
        *,
        base_url: str = "https://overpass-api.de/api/interpreter",
        timeout_seconds: float = 20.0,
        user_agent: str = "agentic-trip/0.1 (local; contact: dev@localhost)",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._user_agent = user_agent

    def fetch_bbox(self, bbox: list[float], country_code: str | None) -> list[PlaceRecord]:
        """bbox = [min_lon, min_lat, max_lon, max_lat]."""
        if not bbox or len(bbox) != 4:
            return []
        min_lon, min_lat, max_lon, max_lat = bbox
        # Overpass uses (south,west,north,east)
        query = (
            f"[out:json][timeout:{int(self._timeout)}];"
            f"("
            f'node["tourism"]({min_lat},{min_lon},{max_lat},{max_lon});'
            f'node["historic"]({min_lat},{min_lon},{max_lat},{max_lon});'
            f");out body 50;"
        )
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(
                    self._base_url,
                    data={"data": query},
                    headers={"User-Agent": self._user_agent},
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError, TypeError):
            return []
        return self._map_elements(payload, country_code)

    def _map_elements(
        self, payload: dict[str, Any], country_code: str | None
    ) -> list[PlaceRecord]:
        elements = payload.get("elements") or []
        places: list[PlaceRecord] = []
        for el in elements:
            if not isinstance(el, dict):
                continue
            lat = el.get("lat")
            lon = el.get("lon")
            if lat is None or lon is None:
                continue
            tags = el.get("tags") or {}
            name = tags.get("name")
            if not name:
                continue
            osm_id = str(el.get("id") or name)
            category = tags.get("tourism") or tags.get("historic") or "poi"
            tag_list = [str(k) for k, v in tags.items() if v]
            places.append(
                PlaceRecord(
                    name=str(name),
                    lon=float(lon),
                    lat=float(lat),
                    provider="overpass",
                    provider_id=osm_id,
                    country_code=country_code,
                    category=str(category),
                    tags=tag_list[:20],
                )
            )
        return places


class OtmAdapter:
    """OpenTripMap-class adapter — fail-soft to empty on timeout/error."""

    def __init__(
        self,
        *,
        base_url: str = "https://api.opentripmap.com/0.1/en/places/bbox",
        api_key: str | None = None,
        timeout_seconds: float = 15.0,
        user_agent: str = "agentic-trip/0.1 (local; contact: dev@localhost)",
    ) -> None:
        self._base_url = base_url
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._user_agent = user_agent

    def fetch_bbox(self, bbox: list[float], country_code: str | None) -> list[PlaceRecord]:
        if not bbox or len(bbox) != 4:
            return []
        if not self._api_key:
            # Unconfigured key → empty (honest), not invented places.
            return []
        min_lon, min_lat, max_lon, max_lat = bbox
        params: dict[str, Any] = {
            "lon_min": min_lon,
            "lat_min": min_lat,
            "lon_max": max_lon,
            "lat_max": max_lat,
            "format": "json",
            "limit": 50,
            "apikey": self._api_key,
        }
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(
                    self._base_url,
                    params=params,
                    headers={"User-Agent": self._user_agent},
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError, TypeError):
            return []
        return self._map_payload(payload, country_code)

    def _map_payload(
        self, payload: Any, country_code: str | None
    ) -> list[PlaceRecord]:
        items = payload if isinstance(payload, list) else payload.get("features") or []
        places: list[PlaceRecord] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            # OTM list format: name, point:{lon,lat}, xid, kinds
            point = item.get("point") or {}
            lon = point.get("lon") if isinstance(point, dict) else item.get("lon")
            lat = point.get("lat") if isinstance(point, dict) else item.get("lat")
            name = item.get("name") or item.get("properties", {}).get("name")
            xid = item.get("xid") or item.get("id") or name
            if lon is None or lat is None or not name:
                continue
            kinds = str(item.get("kinds") or "")
            tags = [k for k in kinds.split(",") if k][:20]
            category = tags[0] if tags else "poi"
            places.append(
                PlaceRecord(
                    name=str(name),
                    lon=float(lon),
                    lat=float(lat),
                    provider="otm",
                    provider_id=str(xid),
                    country_code=country_code,
                    category=category,
                    tags=tags,
                )
            )
        return places
