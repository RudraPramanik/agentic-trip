from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from src.ports import ObsPort


@contextmanager
def _noop() -> Iterator[None]:
    yield


class NoOpObs(ObsPort):
    def start_trace(self, name: str, **kwargs: Any) -> Iterator[None]:
        return _noop()

    def span(self, name: str, **kwargs: Any) -> Iterator[None]:
        return _noop()

    def generation(self, name: str, **kwargs: Any) -> Iterator[None]:
        return _noop()
