"""Narrative id-lock proofs (P4.6)."""

from __future__ import annotations

import pytest

from src.modules.llm.types import LlmUnavailable
from src.modules.planner import Day, Itinerary, Stop, write_narrative


class NarrativeLlm:
    def __init__(self, payload: dict | None = None, *, fail: bool = False) -> None:
        self.payload = payload
        self.fail = fail

    async def complete(self, role: str, messages: list, schema=None):
        assert role == "narrative"
        if self.fail:
            raise RuntimeError("llm down")
        if self.payload is None:
            return LlmUnavailable(role=role)
        return self.payload


@pytest.mark.asyncio
async def test_narrative_preserves_place_ids() -> None:
    itin = Itinerary(
        days=[
            Day(
                day_index=1,
                stops=[Stop(place_id="a", name="A"), Stop(place_id="b", name="B")],
            )
        ]
    )
    llm = NarrativeLlm(
        {
            "days": [
                {
                    "day_index": 1,
                    "title": "Day One",
                    "story": "Nice day",
                    "stops": [
                        {"place_id": "a", "title": "Stop A"},
                        {"place_id": "b", "title": "Stop B"},
                        {"place_id": "invented", "title": "Nope"},
                    ],
                }
            ]
        }
    )
    out = await write_narrative(itin, llm)  # type: ignore[arg-type]
    assert out.stop_place_ids() == {"a", "b"}
    assert out.days[0].title == "Day One"
    assert out.days[0].stops[0].title == "Stop A"


@pytest.mark.asyncio
async def test_narrative_fail_does_not_invent() -> None:
    itin = Itinerary(
        days=[Day(day_index=1, stops=[Stop(place_id="a", name="A")])]
    )
    out = await write_narrative(itin, NarrativeLlm(fail=True))  # type: ignore[arg-type]
    assert out.stop_place_ids() == {"a"}
    assert out.days[0].title is None
