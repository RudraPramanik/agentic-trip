"""Places adapters + facade proofs (P3.2)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.modules.catalog.adapters import OtmAdapter, OverpassAdapter
from src.modules.catalog.facade import DefaultPlacesFacade, FetchResult
from src.modules.catalog.models import PlaceRecord


def test_overpass_maps_elements() -> None:
    adapter = OverpassAdapter()
    payload = {
        "elements": [
            {
                "id": 1,
                "lat": 35.0,
                "lon": 135.0,
                "tags": {"name": "Temple", "tourism": "attraction"},
            },
            {"id": 2, "lat": 35.1, "lon": 135.1, "tags": {}},  # no name
        ]
    }
    places = adapter._map_elements(payload, "jp")
    assert len(places) == 1
    assert places[0].name == "Temple"
    assert places[0].country_code == "jp"
    assert places[0].provider == "overpass"


def test_overpass_timeout_returns_empty() -> None:
    adapter = OverpassAdapter(timeout_seconds=0.01)
    with patch("httpx.Client") as client_cls:
        client = MagicMock()
        client.__enter__.return_value = client
        client.post.side_effect = httpx.TimeoutException("down")
        client_cls.return_value = client
        assert adapter.fetch_bbox([135.0, 34.0, 136.0, 35.0], "jp") == []


def test_otm_without_key_returns_empty() -> None:
    adapter = OtmAdapter(api_key=None)
    assert adapter.fetch_bbox([135.0, 34.0, 136.0, 35.0], "jp") == []


def test_facade_partial_when_provider_raises() -> None:
    class BoomOverpass:
        def fetch_bbox(self, bbox, country_code):
            raise RuntimeError("overpass down")

    class OkOtm:
        def fetch_bbox(self, bbox, country_code):
            return [
                PlaceRecord(
                    name="OK",
                    lon=135.5,
                    lat=34.5,
                    provider="otm",
                    provider_id="1",
                    country_code=country_code,
                )
            ]

    facade = DefaultPlacesFacade(overpass=BoomOverpass(), otm=OkOtm())  # type: ignore[arg-type]
    result = facade.fetch_for_scope(
        {"bbox": [135.0, 34.0, 136.0, 35.0], "country_code": "jp", "kind": "city"}
    )
    assert isinstance(result, FetchResult)
    assert result.partial is True
    assert len(result.places) == 1
    assert result.places[0].name == "OK"


def test_facade_no_bbox_no_centroid() -> None:
    facade = DefaultPlacesFacade(
        overpass=OverpassAdapter(),
        otm=OtmAdapter(api_key=None),
    )
    result = facade.fetch_for_scope({"kind": "country", "hubs": [], "country_code": "jp"})
    assert result.places == []
    assert "no_bbox" in result.errors
