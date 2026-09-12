"""Media facade stub — off generate hot path (P5.6)."""

from __future__ import annotations

from typing import Any, Protocol


class MediaProvider(Protocol):
    async def get_place_media(self, place_id: str) -> list[dict[str, Any]]: ...


class StubMediaProvider:
    """Fail-soft empty media. Never invent venue photo URLs."""

    async def get_place_media(self, place_id: str) -> list[dict[str, Any]]:
        _ = place_id
        return []
