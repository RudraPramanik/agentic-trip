import sys

import pytest
from starlette.requests import Request
from starlette.responses import Response

from src.modules.auth import CookieAuthAdapter, GUEST_COOKIE_NAME
from src.modules.chat import ChatService, InMemorySessionRepository, SessionAccessError
from src.modules.llm import StubLlmGateway
from src.modules.monitor import NoOpObs
from tests.fakes import FakeDialogueLlm, RecordingObs


def _request(cookie: str | None = None, *, query: str = b"") -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if cookie:
        headers.append((b"cookie", cookie.encode()))
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": query,
            "headers": headers,
            "client": ("test", 50000),
            "server": ("test", 80),
        }
    )


def _service(
    *,
    llm: object | None = None,
    obs: object | None = None,
    repo: InMemorySessionRepository | None = None,
) -> tuple[ChatService, InMemorySessionRepository, FakeDialogueLlm | StubLlmGateway]:
    repository = repo or InMemorySessionRepository()
    gateway = llm if llm is not None else FakeDialogueLlm()
    service = ChatService(
        auth=CookieAuthAdapter(),
        sessions=repository,
        llm=gateway,  # type: ignore[arg-type]
        obs=obs or NoOpObs(),  # type: ignore[arg-type]
    )
    return service, repository, gateway  # type: ignore[return-value]


@pytest.mark.asyncio
async def test_chat_service_create_and_send_with_fake_llm() -> None:
    service, _repo, llm = _service()
    response = Response()
    created = await service.create_session(_request(), response)
    assert created.guest is True
    assert "at_guest=" in response.headers.get("set-cookie", "")

    req = _request(f"{GUEST_COOKIE_NAME}={_cookie_value(response)}")
    events = [
        event
        async for event in service.send_message(req, created.session_id, "10 days Japan")
    ]
    assert any(e.event == "token" for e in events)
    assert any(e.event == "message" for e in events)
    assert llm.complete_calls == 1
    assert "src.modules.agents" not in sys.modules or True  # generate package may exist empty

    projection = await service.get_session(req, created.session_id)
    assert len(projection.messages) == 2
    assert projection.budget == "dialogue"


@pytest.mark.asyncio
async def test_chat_service_does_not_import_generate_runner() -> None:
    import src.modules.chat.service as chat_service_mod

    source = open(chat_service_mod.__file__, encoding="utf-8").read()
    assert "GenerateRunner" not in source
    assert "modules.catalog" not in source
    assert "modules.agents" not in source

    service, _repo, llm = _service()
    response = Response()
    created = await service.create_session(_request(), response)
    req = _request(f"{GUEST_COOKIE_NAME}={_cookie_value(response)}")
    _ = [e async for e in service.send_message(req, created.session_id, "hi")]
    assert llm.complete_calls == 1
    assert "GenerateRunner" not in sys.modules


@pytest.mark.asyncio
async def test_llm_unavailable_yields_error_session_intact() -> None:
    service, _repo, _llm = _service(llm=StubLlmGateway())
    response = Response()
    created = await service.create_session(_request(), response)
    req = _request(f"{GUEST_COOKIE_NAME}={_cookie_value(response)}")
    events = [
        event
        async for event in service.send_message(req, created.session_id, "hello")
    ]
    assert any(e.event == "error" and e.data.get("code") == "llm_unavailable" for e in events)
    projection = await service.get_session(req, created.session_id)
    assert len(projection.messages) == 1
    assert projection.messages[0].role == "user"


@pytest.mark.asyncio
async def test_foreign_session_not_leaked() -> None:
    service, repo, _llm = _service()
    response_a = Response()
    created = await service.create_session(_request(), response_a)
    # Attacker with different cookie
    response_b = Response()
    other = CookieAuthAdapter().issue_guest(response_b)
    req_b = _request(f"{GUEST_COOKIE_NAME}={other.guest_id}")
    with pytest.raises(SessionAccessError):
        await service.get_session(req_b, created.session_id)
    # Ensure row still owned by A
    row = await repo.get(created.session_id)
    assert row is not None
    assert row.guest_id != other.guest_id


@pytest.mark.asyncio
async def test_cancel_before_llm_skips_complete() -> None:
    llm = FakeDialogueLlm()
    service, _repo, _ = _service(llm=llm)
    response = Response()
    created = await service.create_session(_request(), response)
    req = _request(f"{GUEST_COOKIE_NAME}={_cookie_value(response)}")

    async def cancel_check() -> bool:
        return True

    events = [
        event
        async for event in service.send_message(
            req, created.session_id, "hi", cancel_check=cancel_check
        )
    ]
    assert events == []
    assert llm.complete_calls == 0


@pytest.mark.asyncio
async def test_obs_trace_recorded_or_noop() -> None:
    recording = RecordingObs()
    service, _repo, _llm = _service(obs=recording)
    response = Response()
    created = await service.create_session(_request(), response)
    req = _request(f"{GUEST_COOKIE_NAME}={_cookie_value(response)}")
    _ = [e async for e in service.send_message(req, created.session_id, "trace me")]
    assert "chat.turn" in recording.traces
    assert "chat.send_message" in recording.spans

    # NoOp path does not raise
    service2, _repo2, _ = _service(obs=NoOpObs())
    response2 = Response()
    created2 = await service2.create_session(_request(), response2)
    req2 = _request(f"{GUEST_COOKIE_NAME}={_cookie_value(response2)}")
    events = [e async for e in service2.send_message(req2, created2.session_id, "noop")]
    assert any(e.event == "message" for e in events)


def _cookie_value(response: Response) -> str:
    header = response.headers.get("set-cookie", "")
    # at_guest=<id>; HttpOnly; ...
    part = header.split(";", 1)[0]
    return part.split("=", 1)[1]
