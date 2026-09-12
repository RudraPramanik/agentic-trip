from typing import Any

from src.modules.llm.types import LlmUnavailable
from src.ports import LlmGateway


class StubLlmGateway(LlmGateway):
    async def complete(
        self,
        role: str,
        messages: list[Any],
        schema: Any | None = None,
    ) -> LlmUnavailable:
        return LlmUnavailable(role=role)

    async def embed(self, texts: list[str]) -> LlmUnavailable:
        return LlmUnavailable(role="embed")
