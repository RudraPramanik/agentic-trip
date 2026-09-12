import json

import pytest
from fastapi.testclient import TestClient

from src.api.sessions import get_chat_service
from src.main import create_app
from src.modules.auth import CookieAuthAdapter, GUEST_COOKIE_NAME
from src.modules.chat import ChatService, InMemorySessionRepository, SchemaUnavailableError
from src.modules.llm import LlmUnavailable, StubLlmGateway
from src.modules.llm.dialogue_stub import LocalDialogueStub
from src.modules.llm.litellm_adapter import LiteLlmAdapter
from src.modules.monitor import NoOpObs
from tests.fakes import (
    FakeDialogueLlm,
    FakeGeoGateway,
    RecordingObs,
    make_chat_service,
    paris_ambiguous,
)


def _client_with_service(
    *,
    llm: FakeDialogueLlm | StubLlmGateway | None = None,
    obs: object | None = None,
    repo: InMemorySessionRepository | None = None,
    geo: FakeGeoGateway | None = None,
) -> tuple[TestClient, ChatService, FakeDialogueLlm | StubLlmGateway]:
    application = create_app()
    service, repository, gateway, _geo, runner = make_chat_service(
        llm=llm, obs=obs, repo=repo, geo=geo
    )
    application.state.dialogue_runner = runner
    application.dependency_overrides[get_chat_service] = lambda: service
    return TestClient(application), service, gateway  # type: ignore[return-value]


def _parse_sse(body: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    current_event = "message"
    for line in body.splitlines():
        if line.startswith("event:"):
            current_event = line.removeprefix("event:").strip()
        elif line.startswith("data:"):
            data = json.loads(line.removeprefix("data:").strip())
            events.append((current_event, data))
    return events


def test_create_session_sets_cookie() -> None:
    client, _, _ = _client_with_service()
    response = client.post("/api/v1/sessions")
    assert response.status_code == 200
    payload = response.json()
    assert "session_id" in payload
    assert payload["guest"] is True
    assert GUEST_COOKIE_NAME in response.cookies


def test_guest_message_sse_round_trip() -> None:
    client, _, llm = _client_with_service()
    created = client.post("/api/v1/sessions")
    session_id = created.json()["session_id"]
    response = client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"text": "10 days in Japan", "user_id": "forged-should-ignore"},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    events = _parse_sse(response.text)
    assert any(name == "token" for name, _ in events)
    assert any(name == "message" for name, _ in events)
    assert isinstance(llm, FakeDialogueLlm)
    assert llm.complete_calls >= 1

    projection = client.get(f"/api/v1/sessions/{session_id}")
    assert projection.status_code == 200
    body = projection.json()
    assert body["session_id"] == session_id
    assert len(body["messages"]) >= 2
    assert body["budget"] == "dialogue"
    assert body["trip_scope"] is not None
    assert body["trip_scope"]["kind"] == "country"


def test_foreign_session_denied() -> None:
    repo = InMemorySessionRepository()
    owner, _, _ = _client_with_service(repo=repo)
    created = owner.post("/api/v1/sessions")
    session_id = created.json()["session_id"]

    attacker, _, _ = _client_with_service(repo=repo)
    attacker.post("/api/v1/sessions")
    denied = attacker.get(f"/api/v1/sessions/{session_id}")
    assert denied.status_code == 404
    assert denied.json() == {"detail": "session not found"}


def test_missing_duration_asks_session_getable() -> None:
    client, _, _ = _client_with_service(llm=StubLlmGateway())
    created = client.post("/api/v1/sessions")
    session_id = created.json()["session_id"]
    response = client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"text": "Japan food"},
    )
    events = _parse_sse(response.text)
    assert any(name == "message" for name, _ in events)
    projection = client.get(f"/api/v1/sessions/{session_id}")
    assert projection.status_code == 200
    assert projection.json()["trip_scope"] is None


def test_unknown_session_not_found() -> None:
    client, _, _ = _client_with_service()
    client.post("/api/v1/sessions")
    response = client.get("/api/v1/sessions/00000000-0000-0000-0000-000000000099")
    assert response.status_code == 404


def test_generate_route_requires_owned_session() -> None:
    client, _, _ = _client_with_service()
    response = client.post("/api/v1/sessions/demo/generate")
    assert response.status_code == 404
    paths = create_app().openapi()["paths"]
    assert "/api/v1/sessions/{session_id}/generate" in paths


def test_hitl_resume_api_sets_trip_scope() -> None:
    geo = FakeGeoGateway({"paris": paris_ambiguous()})
    client, service, _ = _client_with_service(geo=geo)
    created = client.post("/api/v1/sessions")
    session_id = created.json()["session_id"]

    response = client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"text": "4 days in Paris"},
    )
    events = _parse_sse(response.text)
    assert any(name == "hitl" for name, _ in events)

    projection = client.get(f"/api/v1/sessions/{session_id}")
    body = projection.json()
    assert body["hitl"] is not None
    assert body["hitl"]["status"] == "pending"
    choice_id = body["hitl"]["candidates"][0]["choice_id"]

    resumed = client.post(
        f"/api/v1/sessions/{session_id}/hitl",
        json={"choice_id": choice_id},
    )
    assert resumed.status_code == 200
    resumed_body = resumed.json()
    assert resumed_body["trip_scope"] is not None
    assert resumed_body["trip_scope"]["kind"] == "city"
    assert resumed_body["hitl"] is None or resumed_body["hitl"].get("status") == "resolved"


def test_foreign_hitl_resume_denied() -> None:
    geo = FakeGeoGateway({"paris": paris_ambiguous()})
    repo = InMemorySessionRepository()
    owner, _, _ = _client_with_service(repo=repo, geo=geo)
    created = owner.post("/api/v1/sessions")
    session_id = created.json()["session_id"]
    owner.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"text": "4 days in Paris"},
    )

    attacker, _, _ = _client_with_service(repo=repo, geo=geo)
    attacker.post("/api/v1/sessions")
    denied = attacker.post(
        f"/api/v1/sessions/{session_id}/hitl",
        json={"choice_id": "city:paris-fr"},
    )
    assert denied.status_code == 404


def test_hitl_route_is_product_route() -> None:
    client, _, _ = _client_with_service()
    created = client.post("/api/v1/sessions")
    session_id = created.json()["session_id"]
    # No pending hitl → 409, but route exists (not 404).
    response = client.post(
        f"/api/v1/sessions/{session_id}/hitl",
        json={"choice_id": "x"},
    )
    assert response.status_code == 409


def test_obs_recording_on_asgi_turn() -> None:
    obs = RecordingObs()
    client, _, _ = _client_with_service(obs=obs)
    created = client.post("/api/v1/sessions")
    session_id = created.json()["session_id"]
    client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"text": "4 days Kyoto"},
    )
    assert "chat.turn" in obs.traces


class _MissingSchemaRepo(InMemorySessionRepository):
    async def create(self, guest_id: str):
        raise SchemaUnavailableError("Product schema is not applied")


def test_create_session_missing_schema_is_honest_503() -> None:
    client, _, _ = _client_with_service(repo=_MissingSchemaRepo())
    response = client.post("/api/v1/sessions")
    assert response.status_code == 503
    assert response.json() == {
        "detail": {
            "code": "schema_unavailable",
            "message": "Product schema is not applied",
        }
    }


@pytest.mark.asyncio
async def test_create_app_wires_unavailable_gateway_not_canned_stub() -> None:
    application = create_app()
    gateway = application.state.llm_gateway
    assert not isinstance(gateway, LocalDialogueStub)
    result = await gateway.complete(
        "dialogue", [{"role": "user", "content": "Japan food slow"}]
    )
    assert isinstance(result, LlmUnavailable)
    assert not isinstance(result, str)


def test_wired_gateway_missing_duration_asks_no_scope() -> None:
    client, _, _ = _client_with_service(llm=LiteLlmAdapter(api_key=None))
    created = client.post("/api/v1/sessions")
    session_id = created.json()["session_id"]
    response = client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"text": "Japan food slow"},
    )
    events = _parse_sse(response.text)
    messages = [data.get("content") for name, data in events if name == "message"]
    assert messages
    assert any("days" in str(content).lower() for content in messages)
    projection = client.get(f"/api/v1/sessions/{session_id}")
    assert projection.status_code == 200
    assert projection.json()["trip_scope"] is None
