"""P2.9 scope goldens — offline asserts for bible cases."""

import pytest

from src.modules.agents.dialogue import DialogueDeps, DialogueRunner
from src.modules.agents.intent import parse_intent
from src.modules.geo.scope import classify_scope
from src.modules.geo.service import GeoService
from src.modules.geo.types import AskClarification, TripIntent, TripScope
from src.modules.llm import StubLlmGateway
from langgraph.checkpoint.memory import InMemorySaver

from tests.fakes import (
    FakeDialogueLlm,
    FakeGeoGateway,
    default_geo_map,
    japan_country,
    kyoto_city,
    paris_ambiguous,
    tuscany_region,
)


@pytest.mark.asyncio
async def test_golden_city_kyoto_4d() -> None:
    intent = TripIntent(place_query="Kyoto", duration_days=4, raw_text="4 days Kyoto")
    scope = classify_scope(intent, kyoto_city())
    assert isinstance(scope, TripScope)
    assert scope.kind == "city"


@pytest.mark.asyncio
async def test_golden_tuscany_region() -> None:
    intent = TripIntent(place_query="Tuscany", duration_days=7)
    scope = classify_scope(intent, tuscany_region())
    assert isinstance(scope, TripScope)
    assert scope.kind == "region"


@pytest.mark.asyncio
async def test_golden_country_short_japan_3d() -> None:
    intent = TripIntent(place_query="Japan", duration_days=3)
    scope = classify_scope(intent, japan_country())
    assert isinstance(scope, TripScope)
    assert scope.kind == "region"
    assert scope.hubs


@pytest.mark.asyncio
async def test_golden_kyoto_wins() -> None:
    parsed = await parse_intent("3 days in Kyoto", StubLlmGateway())
    assert isinstance(parsed, TripIntent)
    scope = classify_scope(parsed, kyoto_city())
    assert isinstance(scope, TripScope)
    assert scope.kind == "city"


@pytest.mark.asyncio
async def test_golden_japan_10_days_or_hitl() -> None:
    intent = TripIntent(place_query="Japan", duration_days=10)
    scope = classify_scope(intent, japan_country())
    assert isinstance(scope, TripScope)
    assert scope.kind == "country"
    assert scope.hubs, "Japan 10d must write hubs (or would be HITL)"


@pytest.mark.asyncio
async def test_golden_ambiguous_paris() -> None:
    runner = DialogueRunner(
        DialogueDeps(
            llm=FakeDialogueLlm(),
            geo=GeoService(FakeGeoGateway({"paris": paris_ambiguous()})),
        ),
        checkpointer=InMemorySaver(),
    )
    outcome = await runner.run_turn("golden-paris", "5 days Paris")
    assert outcome.status == "hitl"
    assert outcome.trip_scope is None


@pytest.mark.asyncio
async def test_golden_missing_duration_ask_no_persist() -> None:
    parsed = await parse_intent("Japan food slow", StubLlmGateway())
    assert isinstance(parsed, AskClarification)

    runner = DialogueRunner(
        DialogueDeps(
            llm=StubLlmGateway(),
            geo=GeoService(FakeGeoGateway(default_geo_map())),
        ),
        checkpointer=InMemorySaver(),
    )
    outcome = await runner.run_turn("golden-ask", "Japan food slow")
    assert outcome.status == "ask"
    assert outcome.trip_scope is None
