import inspect

from src.ports import (
    AuthPort,
    GenerateRunner,
    GeoGateway,
    LlmGateway,
    ObsPort,
    PlaceRepository,
    TravelEngine,
)


def test_ports_import_without_side_effects() -> None:
    for port in (
        LlmGateway,
        AuthPort,
        ObsPort,
        GeoGateway,
        GenerateRunner,
        TravelEngine,
        PlaceRepository,
    ):
        assert inspect.isabstract(port)


def test_llm_gateway_declares_complete_and_embed() -> None:
    assert hasattr(LlmGateway, "complete")
    assert hasattr(LlmGateway, "embed")
