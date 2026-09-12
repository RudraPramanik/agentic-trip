from dataclasses import dataclass
from typing import Any

from src.ports import LlmGateway


@dataclass(frozen=True)
class LlmUnavailable:
    role: str
    reason: str = "unconfigured"


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
