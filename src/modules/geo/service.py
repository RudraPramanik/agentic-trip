from __future__ import annotations

from src.modules.geo.types import GeoSearchResult
from src.ports import GeoGateway


class GeoService:
    """Dialogue-facing geo search — never silently picks a country centroid."""

    def __init__(self, gateway: GeoGateway) -> None:
        self._gateway = gateway

    def geocode_search(self, query: str) -> GeoSearchResult:
        candidates = self._gateway.search(query)
        return GeoSearchResult(candidates=list(candidates), query=query)


def geocode_search(gateway: GeoGateway, query: str) -> GeoSearchResult:
    return GeoService(gateway).geocode_search(query)
