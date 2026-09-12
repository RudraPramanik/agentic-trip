from abc import ABC, abstractmethod
from typing import Any

from starlette.requests import Request
from starlette.responses import Response


class LlmGateway(ABC):
    @abstractmethod
    async def complete(
        self,
        role: str,
        messages: list[Any],
        schema: Any | None = None,
    ) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def embed(self, texts: list[str]) -> Any:
        raise NotImplementedError


class AuthPort(ABC):
    @abstractmethod
    def issue_guest(self, response: Response) -> Any:
        raise NotImplementedError

    @abstractmethod
    def read_principal(self, request: Request) -> Any:
        raise NotImplementedError


class ObsPort(ABC):
    @abstractmethod
    def start_trace(self, name: str, **kwargs: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def span(self, name: str, **kwargs: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def generation(self, name: str, **kwargs: Any) -> Any:
        raise NotImplementedError


class GeoGateway(ABC):
    @abstractmethod
    def search(self, query: str) -> list[Any]:
        raise NotImplementedError


class GenerateRunner(ABC):
    @abstractmethod
    async def start(self, session_id: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def abort(self, session_id: str) -> Any:
        raise NotImplementedError


class TravelEngine(ABC):
    @abstractmethod
    def pack(self, scope: Any, places: Any, prefs: Any) -> Any:
        raise NotImplementedError


class PlaceRepository(ABC):
    @abstractmethod
    def retrieve(self, scope: Any, prefs: Any) -> Any:
        raise NotImplementedError
