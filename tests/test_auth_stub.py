from starlette.requests import Request
from starlette.responses import Response

from src.modules.auth import GUEST_COOKIE_NAME, StubAuthAdapter


def _request_with_cookie(guest_id: str) -> Request:
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [(b"cookie", f"{GUEST_COOKIE_NAME}={guest_id}".encode())],
            "client": ("test", 50000),
            "server": ("test", 80),
        }
    )


def test_issue_and_read_guest_round_trip() -> None:
    adapter = StubAuthAdapter()
    response = Response()
    issued = adapter.issue_guest(response)
    cookie_header = response.headers.get("set-cookie", "").lower()
    assert GUEST_COOKIE_NAME == "at_guest"
    assert "at_guest=" in cookie_header
    assert "httponly" in cookie_header
    assert "samesite=lax" in cookie_header
    assert "wandr_session" not in cookie_header
    read = adapter.read_principal(_request_with_cookie(issued.guest_id))
    assert read is not None
    assert read.guest_id == issued.guest_id
