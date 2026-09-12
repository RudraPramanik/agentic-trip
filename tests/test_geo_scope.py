from unittest.mock import MagicMock

import httpx
import pytest

from src.modules.geo import GeoService, NominatimAdapter, classify_scope, geocode_search
from src.modules.geo.types import GeoCandidate, NeedsHitl, TripIntent, TripScope
from tests.fakes import (
    FakeGeoGateway,
    japan_country,
    kyoto_city,
    meghalaya_region,
    tuscany_region,
)


def test_nominatim_timeout_returns_empty() -> None:
    client = MagicMock()
    client.get.side_effect = httpx.TimeoutException("timeout", request=MagicMock())
    adapter = NominatimAdapter(client=client, timeout_seconds=0.01)
    assert adapter.search("Paris") == []


def test_nominatim_http_error_returns_empty() -> None:
    client = MagicMock()
    response = MagicMock()
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "err", request=MagicMock(), response=MagicMock(status_code=500)
    )
    client.get.return_value = response
    adapter = NominatimAdapter(client=client)
    assert adapter.search("Paris") == []


def test_nominatim_parses_candidates() -> None:
    client = MagicMock()
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = [
        {
            "lat": "35.01",
            "lon": "135.77",
            "name": "Kyoto",
            "display_name": "Kyoto, Japan",
            "osm_type": "relation",
            "osm_id": 1,
            "addresstype": "city",
            "boundingbox": ["34.9", "35.1", "135.6", "135.9"],
            "address": {"country_code": "jp", "city": "Kyoto"},
        }
    ]
    client.get.return_value = response
    adapter = NominatimAdapter(client=client)
    candidates = adapter.search("Kyoto")
    assert len(candidates) == 1
    assert candidates[0].place_class == "city"
    assert candidates[0].name == "Kyoto"


def test_geocode_search_zero_one_many() -> None:
    empty = FakeGeoGateway({"nowhere": []})
    empty.results["nowhere"] = []
    # Force empty for any query
    class EmptyGeo(FakeGeoGateway):
        def search(self, query: str) -> list[GeoCandidate]:
            return []

    zero = geocode_search(EmptyGeo(), "xyz")
    assert zero.count == 0
    assert zero.needs_hitl

    one = GeoService(FakeGeoGateway({"kyoto": [kyoto_city()]})).geocode_search("Kyoto")
    assert one.count == 1
    assert not one.needs_hitl

    many_gw = FakeGeoGateway(
        {
            "paris": [
                kyoto_city(),
                GeoCandidate(
                    geo_id="city:other",
                    name="Other",
                    display_name="Other",
                    lat=1.0,
                    lon=1.0,
                    place_class="city",
                ),
            ]
        }
    )
    many = GeoService(many_gw).geocode_search("paris")
    assert many.count == 2
    assert many.needs_hitl


def test_classify_scope_kyoto_city() -> None:
    intent = TripIntent(place_query="Kyoto", duration_days=4, vibe=[], raw_text="4 days Kyoto")
    result = classify_scope(intent, kyoto_city())
    assert isinstance(result, TripScope)
    assert result.kind == "city"
    assert result.name == "Kyoto"


def test_classify_scope_meghalaya_region() -> None:
    intent = TripIntent(place_query="Meghalaya", duration_days=5)
    result = classify_scope(intent, meghalaya_region())
    assert isinstance(result, TripScope)
    assert result.kind == "region"


def test_classify_scope_japan_3d_best_region() -> None:
    intent = TripIntent(place_query="Japan", duration_days=3)
    result = classify_scope(intent, japan_country())
    assert isinstance(result, TripScope)
    assert result.kind == "region"
    assert result.explain and "short" in result.explain.lower()


def test_classify_scope_japan_10d_hubs_or_hitl() -> None:
    intent = TripIntent(place_query="Japan", duration_days=10)
    result = classify_scope(intent, japan_country())
    if isinstance(result, TripScope):
        assert result.kind == "country"
        assert result.hubs, "country-long must write hubs[] or HITL"
    else:
        assert isinstance(result, NeedsHitl)


def test_classify_scope_tuscany_region() -> None:
    intent = TripIntent(place_query="Tuscany", duration_days=6)
    result = classify_scope(intent, tuscany_region())
    assert isinstance(result, TripScope)
    assert result.kind == "region"


def test_named_city_wins_over_country() -> None:
    intent = TripIntent(place_query="3 days in Kyoto", duration_days=3)
    result = classify_scope(intent, kyoto_city())
    assert isinstance(result, TripScope)
    assert result.kind == "city"
