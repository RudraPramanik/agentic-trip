from __future__ import annotations

import json
from typing import Any

from src.modules.llm.types import LlmUnavailable
from src.ports import LlmGateway


class LiteLlmAdapter(LlmGateway):
    """Live LiteLLM complete when a provider key exists; structured unavailable otherwise."""

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str = "gpt-4o-mini",
        api_base: str | None = None,
        role_models: dict[str, str] | None = None,
    ) -> None:
        self._api_key = (api_key or "").strip() or None
        self._default_model = model
        self._api_base = (api_base or "").strip() or None
        self._role_models = role_models or {
            "dialogue": model,
            "narrative": model,
            "embed": "text-embedding-3-small",
        }

    @property
    def configured(self) -> bool:
        return self._api_key is not None

    async def complete(
        self,
        role: str,
        messages: list[Any],
        schema: Any | None = None,
    ) -> Any:
        if not self._api_key:
            return LlmUnavailable(role=role, reason="unconfigured")

        import litellm

        model = self._role_models.get(role, self._default_model)
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "api_key": self._api_key,
        }
        if self._api_base:
            kwargs["api_base"] = self._api_base
        if schema is not None:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_out",
                    "schema": schema,
                    "strict": True,
                },
            }

        try:
            response = await litellm.acompletion(**kwargs)
        except Exception as exc:  # noqa: BLE001 — map vendor failures to unavailable
            return LlmUnavailable(role=role, reason=f"provider_error:{type(exc).__name__}")

        content = response.choices[0].message.content  # type: ignore[index]
        if schema is not None and isinstance(content, str):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return content
        return content

    async def embed(self, texts: list[str]) -> Any:
        if not self._api_key:
            return LlmUnavailable(role="embed", reason="unconfigured")
        import litellm

        model = self._role_models.get("embed", "text-embedding-3-small")
        try:
            response = await litellm.aembedding(
                model=model, input=texts, api_key=self._api_key
            )
            return [item["embedding"] for item in response.data]  # type: ignore[index]
        except Exception as exc:  # noqa: BLE001
            return LlmUnavailable(role="embed", reason=f"provider_error:{type(exc).__name__}")


def build_llm_gateway(
    *,
    api_key: str | None,
    model: str = "gpt-4o-mini",
    api_base: str | None = None,
    embedding_model: str | None = None,
    dialogue_stub_fallback: bool = True,
) -> LlmGateway:
    """Composition helper: live adapter when keyed; else local dialogue stub."""
    key = (api_key or "").strip() or None
    role_models = {
        "dialogue": model,
        "narrative": model,
        "embed": embedding_model or "text-embedding-3-small",
    }
    if key:
        return LiteLlmAdapter(
            api_key=key,
            model=model,
            api_base=api_base,
            role_models=role_models,
        )
    if dialogue_stub_fallback:
        from src.modules.llm.dialogue_stub import LocalDialogueStub

        return LocalDialogueStub()
    return LiteLlmAdapter(
        api_key=None,
        model=model,
        api_base=api_base,
        role_models=role_models,
    )
