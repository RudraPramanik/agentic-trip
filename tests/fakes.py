from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from src.modules.agents.dialogue import DialogueDeps, DialogueRunner
from src.modules.chat import ChatService, InMemorySessionRepository
from src.modules.auth import CookieAuthAdapter
from src.modules.geo.service import GeoService
from src.modules.geo.types import GeoCandidate
from src.modules.monitor import NoOpObs
from src.ports import GeoGateway, ObsPort


class RecordingObs(ObsPort):
    def __init__(self) -> None:
        self.traces: list[str] = []
        self.spans: list[str] = []
        self.span_kwargs: list[dict[str, Any]] = []

    @contextmanager
    def start_trace(self, name: str, **kwargs: Any) -> Iterator[None]:
        self.traces.append(name)
        yield

    @contextmanager
    def span(self, name: str, **kwargs: Any) -> Iterator[None]:
        self.spans.append(name)
        self.span_kwargs.append(dict(kwargs))
        yield

    @contextmanager
    def generation(self, name: str, **kwargs: Any) -> Iterator[None]:
        yield


class FakeDialogueLlm:
    """Test double that returns fixed dialogue text and counts complete calls."""

    def __init__(
        self,
        *,
        text: str = "hello from fake llm",
        structured: dict[str, Any] | None = None,
    ) -> None:
        self.text = text
        self.structured = structured
        self.complete_calls = 0

    async def complete(
        self,
        role: str,
        messages: list[Any],
        schema: Any | None = None,
    ) -> Any:
        self.complete_calls += 1
        if schema is not None and self.structured is not None:
            return self.structured
        return self.text

    async def embed(self, texts: list[str]) -> Any:
        raise NotImplementedError


class FakeGeoGateway(GeoGateway):
    """Deterministic geo search for tests — never hits Nominatim."""

    def __init__(self, results: dict[str, list[GeoCandidate]] | None = None) -> None:
        self.results = results or {}
        self.calls: list[str] = []

    def search(self, query: str) -> list[GeoCandidate]:
        self.calls.append(query)
        key = query.strip().lower()
        for k, candidates in self.results.items():
            if k.lower() in key or key in k.lower():
                return list(candidates)
        # Default: single city candidate named after query
        if not key:
            return []
        return [
            GeoCandidate(
                geo_id=f"test:{key}",
                name=query.strip().title(),
                display_name=f"{query.strip().title()}, Testland",
                lat=35.0,
                lon=135.0,
                place_class="city",
                admin_level=8,
                bbox=[134.5, 34.5, 135.5, 35.5],
                country_code="xx",
            )
        ]


def japan_country() -> GeoCandidate:
    return GeoCandidate(
        geo_id="country:japan",
        name="Japan",
        display_name="Japan",
        lat=36.0,
        lon=138.0,
        place_class="country",
        admin_level=2,
        bbox=[129.0, 30.0, 146.0, 46.0],
        country_code="jp",
    )


def kyoto_city() -> GeoCandidate:
    return GeoCandidate(
        geo_id="city:kyoto",
        name="Kyoto",
        display_name="Kyoto, Kyoto Prefecture, Japan",
        lat=35.01,
        lon=135.77,
        place_class="city",
        admin_level=8,
        bbox=[135.6, 34.9, 135.9, 35.1],
        country_code="jp",
    )


def tuscany_region() -> GeoCandidate:
    return GeoCandidate(
        geo_id="region:tuscany",
        name="Tuscany",
        display_name="Tuscany, Italy",
        lat=43.77,
        lon=11.25,
        place_class="region",
        admin_level=4,
        bbox=[10.0, 42.0, 12.5, 44.5],
        country_code="it",
    )


def meghalaya_region() -> GeoCandidate:
    return GeoCandidate(
        geo_id="region:meghalaya",
        name="Meghalaya",
        display_name="Meghalaya, India",
        lat=25.5,
        lon=91.3,
        place_class="region",
        admin_level=4,
        bbox=[89.8, 25.0, 92.8, 26.1],
        country_code="in",
    )


def paris_ambiguous() -> list[GeoCandidate]:
    return [
        GeoCandidate(
            geo_id="city:paris-fr",
            name="Paris",
            display_name="Paris, France",
            lat=48.85,
            lon=2.35,
            place_class="city",
            admin_level=8,
            bbox=[2.2, 48.8, 2.5, 48.9],
            country_code="fr",
        ),
        GeoCandidate(
            geo_id="city:paris-tx",
            name="Paris",
            display_name="Paris, Texas, United States",
            lat=33.66,
            lon=-95.55,
            place_class="city",
            admin_level=8,
            bbox=[-95.6, 33.6, -95.5, 33.7],
            country_code="us",
        ),
    ]


def default_geo_map() -> dict[str, list[GeoCandidate]]:
    return {
        "japan": [japan_country()],
        "kyoto": [kyoto_city()],
        "tuscany": [tuscany_region()],
        "meghalaya": [meghalaya_region()],
        "paris": paris_ambiguous(),
    }


def make_dialogue_runner(
    *,
    llm: object | None = None,
    geo: FakeGeoGateway | None = None,
) -> tuple[DialogueRunner, FakeDialogueLlm | Any, FakeGeoGateway]:
    gateway = llm if llm is not None else FakeDialogueLlm()
    geo_gw = geo or FakeGeoGateway(default_geo_map())
    runner = DialogueRunner(
        DialogueDeps(llm=gateway, geo=GeoService(geo_gw)),  # type: ignore[arg-type]
        checkpointer=InMemorySaver(),
    )
    return runner, gateway, geo_gw


def make_chat_service(
    *,
    llm: object | None = None,
    obs: object | None = None,
    repo: InMemorySessionRepository | None = None,
    geo: FakeGeoGateway | None = None,
) -> tuple[ChatService, InMemorySessionRepository, Any, FakeGeoGateway, DialogueRunner]:
    repository = repo or InMemorySessionRepository()
    runner, gateway, geo_gw = make_dialogue_runner(llm=llm, geo=geo)
    service = ChatService(
        auth=CookieAuthAdapter(),
        sessions=repository,
        obs=obs or NoOpObs(),  # type: ignore[arg-type]
        dialogue=runner,
    )
    return service, repository, gateway, geo_gw, runner
