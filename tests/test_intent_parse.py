import pytest

from src.modules.agents.intent import parse_intent
from src.modules.geo.types import AskClarification, TripIntent
from src.modules.llm import LiteLlmAdapter, StubLlmGateway
from tests.fakes import FakeDialogueLlm


@pytest.mark.asyncio
async def test_parse_intent_rich_prompt_fills_duration_and_vibe() -> None:
    llm = FakeDialogueLlm(
        structured={
            "place_query": "Japan",
            "duration_days": 10,
            "vibe": ["food", "slow"],
            "constraints": [],
        }
    )
    result = await parse_intent("10 days Japan food slow", llm)
    assert isinstance(result, TripIntent)
    assert result.duration_days == 10
    assert "food" in result.vibe
    assert "slow" in result.vibe
    assert "japan" in result.place_query.lower()


@pytest.mark.asyncio
async def test_parse_intent_missing_duration_asks() -> None:
    llm = FakeDialogueLlm(
        structured={
            "place_query": "Japan",
            "duration_days": None,
            "vibe": ["food"],
            "constraints": [],
        }
    )
    result = await parse_intent("Japan food", llm)
    assert isinstance(result, AskClarification)
    assert "duration" in result.missing


@pytest.mark.asyncio
async def test_parse_intent_missing_keys_heuristic_not_crash() -> None:
    result = await parse_intent("10 days Japan food slow", StubLlmGateway())
    assert isinstance(result, TripIntent)
    assert result.duration_days == 10
    assert "food" in result.vibe


@pytest.mark.asyncio
async def test_lite_llm_adapter_unconfigured_returns_unavailable() -> None:
    adapter = LiteLlmAdapter(api_key=None)
    out = await adapter.complete("dialogue", [{"role": "user", "content": "hi"}])
    from src.modules.llm.types import LlmUnavailable

    assert isinstance(out, LlmUnavailable)
    # Import + call must not raise
    embed = await adapter.embed(["a"])
    assert isinstance(embed, LlmUnavailable)
