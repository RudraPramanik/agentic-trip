from typing import Any

from src.modules.llm.types import LlmUnavailable
from src.ports import LlmGateway


class LocalDialogueStub(LlmGateway):
    """P1 local dialogue stub — returns canned text, never invents trip structure."""

    async def complete(
        self,
        role: str,
        messages: list[Any],
        schema: Any | None = None,
    ) -> str | LlmUnavailable:
        if role != "dialogue":
            return LlmUnavailable(role=role, reason="unsupported_role")
        last_user = ""
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                last_user = str(message.get("content", ""))
                break
        return (
            "Local dialogue stub (no live LLM). "
            f"I heard: {last_user or '(empty)'}. "
            "Tell me more about the trip you want — generate is not available on this turn."
        )

    async def embed(self, texts: list[str]) -> LlmUnavailable:
        return LlmUnavailable(role="embed")
