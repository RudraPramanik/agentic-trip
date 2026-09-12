#!/usr/bin/env python
"""Local terminal smoke for generate SSE (P4 task 11.2).

Usage:

  uv run python scripts/smoke_generate.py

Uses ASGI TestClient + in-memory fakes (same proofs as tests/test_generate_api.py).
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://at:at@localhost:5432/at"
)


def main() -> int:
    from tests.test_generate_api import (
        _build_generate_client,
        _parse_sse,
    )
    from src.modules.catalog.models import PlaceRecord

    client, sessions, places = _build_generate_client()
    create = client.post("/api/v1/sessions")
    assert create.status_code == 200, create.text
    session_id = create.json()["session_id"]

    async def prepare() -> None:
        state = await sessions.get(session_id)
        assert state is not None
        state.trip_scope = {
            "kind": "city",
            "bbox": [135.0, 34.0, 136.0, 35.0],
            "country_code": "jp",
            "day_budget": 2,
        }
        state.intent = {"duration_days": 2}
        await sessions.save(state)
        await places.upsert_many(
            [
                PlaceRecord(
                    name="Spot A",
                    lon=135.5,
                    lat=34.5,
                    provider="t",
                    provider_id="a",
                    country_code="jp",
                ),
                PlaceRecord(
                    name="Spot B",
                    lon=135.55,
                    lat=34.55,
                    provider="t",
                    provider_id="b",
                    country_code="jp",
                ),
            ]
        )

    asyncio.run(prepare())

    abort = client.post(f"/api/v1/sessions/{session_id}/generate/abort")
    assert abort.status_code == 200 and abort.json()["abort_requested"]

    response = client.post(f"/api/v1/sessions/{session_id}/generate")
    assert response.status_code == 200, response.text
    events = _parse_sse(response.text)
    kinds = [e for e, _ in events]
    print("SSE events:", kinds)
    assert "progress" in kinds
    assert "done" in kinds

    async def check_draft() -> None:
        state = await sessions.get(session_id)
        assert state is not None
        assert state.itinerary is not None
        assert state.itinerary["status"] == "draft"
        print(
            "Draft days:",
            len(state.itinerary.get("days") or []),
            "stops:",
            len(state.itinerary.get("place_ids") or []),
        )

    asyncio.run(check_draft())
    print("smoke_generate OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
