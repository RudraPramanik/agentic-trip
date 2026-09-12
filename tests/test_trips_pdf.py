"""P5b: no server PDF route; export-only path remains product."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.main import create_app
from tests.test_trips_api import _build_trips_client


def test_trip_pdf_route_not_shipped() -> None:
    client, _sessions, _repo, _trips = _build_trips_client()
    created = client.post("/api/v1/sessions")
    assert created.status_code == 200
    res = client.get("/api/v1/trips/any-id/pdf")
    assert res.status_code == 404


def test_export_still_product_after_p5b() -> None:
    """OpenAPI still lists trip get/export; PDF path is absent."""
    client = TestClient(create_app())
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/trips/{trip_id}/export" in paths
    assert "/api/v1/trips/{trip_id}" in paths
    assert "/api/v1/trips/{trip_id}/pdf" not in paths
