#!/usr/bin/env python
"""Local terminal smoke for revise SSE (P6 task 7.1).

Usage:

  uv run python scripts/smoke_revise.py

Uses ASGI TestClient + in-memory fakes (same proofs as tests/test_revise_api.py).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://at:at@localhost:5432/at"
)


def main() -> int:
    from tests.test_revise_api import (
        _build_revise_client,
        _parse_sse,
        _seed_draft,
    )

    client, sessions, places = _build_revise_client()
    session_id = _seed_draft(client, sessions, places)

    abort = client.post(f"/api/v1/sessions/{session_id}/generate/abort")
    assert abort.status_code == 200 and abort.json()["abort_requested"]

    response = client.post(
        f"/api/v1/sessions/{session_id}/revise",
        json={"text": "less walking day 2"},
    )
    assert response.status_code == 200, response.text
    events = _parse_sse(response.text)
    kinds = [e for e, _ in events]
    print("SSE events:", kinds)
    assert "progress" in kinds
    assert "done" in kinds

    import asyncio

    async def check() -> None:
        state = await sessions.get(session_id)
        assert state is not None
        assert state.itinerary is not None
        assert state.itinerary["status"] == "draft"
        print(
            "Revised days:",
            len(state.itinerary.get("days") or []),
            "stops:",
            len(state.itinerary.get("place_ids") or []),
            "trip_id:",
            state.trip_id,
        )

    asyncio.run(check())
    print("smoke_revise OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
