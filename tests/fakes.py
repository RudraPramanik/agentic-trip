from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from src.ports import ObsPort


class RecordingObs(ObsPort):
    def __init__(self) -> None:
        self.traces: list[str] = []
        self.spans: list[str] = []

    @contextmanager
    def start_trace(self, name: str, **kwargs: Any) -> Iterator[None]:
        self.traces.append(name)
        yield

    @contextmanager
    def span(self, name: str, **kwargs: Any) -> Iterator[None]:
        self.spans.append(name)
        yield

    @contextmanager
    def generation(self, name: str, **kwargs: Any) -> Iterator[None]:
        yield


class FakeDialogueLlm:
    """Test double that returns fixed dialogue text and counts complete calls."""

    def __init__(self, *, text: str = "hello from fake llm") -> None:
        self.text = text
        self.complete_calls = 0

    async def complete(
        self,
        role: str,
        messages: list[Any],
        schema: Any | None = None,
    ) -> str:
        self.complete_calls += 1
        return self.text

    async def embed(self, texts: list[str]) -> Any:
        raise NotImplementedError
