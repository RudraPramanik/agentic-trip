import pytest

from src.modules.llm import LlmUnavailable, StubLlmGateway


def test_import_llm_without_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    import src.modules.llm as llm_module

    assert llm_module.StubLlmGateway is StubLlmGateway


@pytest.mark.asyncio
async def test_complete_without_keys_returns_unavailable() -> None:
    result = await StubLlmGateway().complete("dialogue", [{"role": "user", "content": "hi"}])
    assert isinstance(result, LlmUnavailable)
    assert result.role == "dialogue"
    assert result.reason == "unconfigured"


@pytest.mark.asyncio
async def test_embed_without_keys_returns_unavailable() -> None:
    result = await StubLlmGateway().embed(["hello"])
    assert isinstance(result, LlmUnavailable)
    assert result.reason == "unconfigured"
