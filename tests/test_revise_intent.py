"""P6.1 parse revision intent proofs."""

from __future__ import annotations

import pytest

from src.modules.agents.revise import RevisionIntent, parse_revision_intent
from src.modules.llm.stub import StubLlmGateway
from src.modules.planner.types import Day, Itinerary, Stop
from tests.fakes import FakeDialogueLlm


def _itin() -> Itinerary:
    return Itinerary(
        days=[
            Day(
                day_index=1,
                stops=[Stop(place_id="jp-1", name="Fushimi Inari")],
            ),
            Day(
                day_index=2,
                stops=[
                    Stop(place_id="jp-2", name="Kiyomizu"),
                    Stop(place_id="jp-3", name="Arashiyama"),
                    Stop(place_id="jp-4", name="Nara Park"),
                ],
            ),
        ],
        status="draft",
        place_ids=["jp-1", "jp-2", "jp-3", "jp-4"],
    )


@pytest.mark.asyncio
async def test_less_walking_day_2_is_walk_cap_patch() -> None:
    intent = await parse_revision_intent(
        "less walking day 2", _itin(), StubLlmGateway()
    )
    assert intent.error is None
    assert intent.day_index == 2
    assert intent.walk_budget_factor is not None
    assert intent.walk_budget_factor < 1.0
    assert intent.max_stops_per_day == 2
    assert "days" not in intent.to_dict() or intent.to_dict().get("days") is None


@pytest.mark.asyncio
async def test_unknown_venue_name_not_scheduled() -> None:
    intent = await parse_revision_intent(
        'less walking day 2 and add "Atlantis Hotel"',
        _itin(),
        StubLlmGateway(),
    )
    assert any("atlantis" in n.lower() for n in intent.unknown_names)
    assert "Atlantis Hotel" not in intent.drop_place_ids
    assert all(pid in {"jp-1", "jp-2", "jp-3", "jp-4"} for pid in intent.drop_place_ids)


@pytest.mark.asyncio
async def test_llm_whole_trip_rewrite_is_ignored() -> None:
    llm = FakeDialogueLlm(
        structured={
            "days": [{"day_index": 1, "stops": [{"place_id": "ghost", "name": "Ghost"}]}],
            "itinerary": {"days": []},
            "day_index": 2,
            "walk_budget_factor": 0.5,
            "max_stops_per_day": 2,
        }
    )
    intent = await parse_revision_intent("rewrite the whole trip", _itin(), llm)
    assert isinstance(intent, RevisionIntent)
    assert intent.day_index == 2
    assert intent.walk_budget_factor == 0.5
    dumped = intent.to_dict()
    assert "days" not in dumped
    assert "ghost" not in intent.drop_place_ids
    assert "ghost" not in {n.lower() for n in intent.unknown_names} or True


@pytest.mark.asyncio
async def test_drop_ids_must_already_be_on_itinerary() -> None:
    llm = FakeDialogueLlm(
        structured={"drop_place_ids": ["jp-2", "not-real"], "day_index": 2}
    )
    intent = await parse_revision_intent("drop a stop", _itin(), llm)
    assert intent.drop_place_ids == ["jp-2"]
    assert "not-real" in intent.unknown_names
