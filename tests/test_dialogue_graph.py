import pytest
from langgraph.checkpoint.memory import InMemorySaver

from src.modules.agents.dialogue import DialogueDeps, DialogueRunner
from src.modules.geo.service import GeoService
from src.modules.llm import StubLlmGateway
from tests.fakes import FakeGeoGateway, FakeDialogueLlm, paris_ambiguous


@pytest.mark.asyncio
async def test_ambiguous_paris_interrupts() -> None:
    geo = FakeGeoGateway({"paris": paris_ambiguous()})
    runner = DialogueRunner(
        DialogueDeps(llm=FakeDialogueLlm(), geo=GeoService(geo)),
        checkpointer=InMemorySaver(),
    )
    outcome = await runner.run_turn("sess-paris", "4 days in Paris")
    assert outcome.status == "hitl"
    assert outcome.hitl is not None
    assert outcome.hitl["status"] == "pending"
    assert len(outcome.hitl["candidates"]) >= 2
    assert outcome.trip_scope is None


@pytest.mark.asyncio
async def test_paris_resume_confirms_city() -> None:
    geo = FakeGeoGateway({"paris": paris_ambiguous()})
    runner = DialogueRunner(
        DialogueDeps(llm=FakeDialogueLlm(), geo=GeoService(geo)),
        checkpointer=InMemorySaver(),
    )
    session_id = "sess-paris-resume"
    pending = await runner.run_turn(session_id, "4 days in Paris")
    assert pending.status == "hitl"
    choice = pending.hitl["candidates"][0]["choice_id"]
    confirmed = await runner.resume(session_id, choice_id=choice, text=None)
    assert confirmed.status == "confirmed"
    assert confirmed.trip_scope is not None
    assert confirmed.trip_scope["kind"] == "city"


@pytest.mark.asyncio
async def test_checkpoint_failure_honest_error() -> None:
    class BrokenSaver(InMemorySaver):
        def put(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("checkpoint store down")

        async def aput(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("checkpoint store down")

    geo = FakeGeoGateway({"paris": paris_ambiguous()})
    runner = DialogueRunner(
        DialogueDeps(llm=StubLlmGateway(), geo=GeoService(geo)),
        checkpointer=BrokenSaver(),
    )
    outcome = await runner.run_turn("sess-broken", "4 days in Paris")
    assert outcome.status == "error"
    assert outcome.error_code in {"checkpoint_or_graph_error", "checkpoint_unavailable"}
