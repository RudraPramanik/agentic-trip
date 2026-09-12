import os
from dataclasses import dataclass
from uuid import uuid4

from starlette.requests import Request
from starlette.responses import Response

from src.ports import AuthPort

GUEST_COOKIE_NAME = "at_guest"


@dataclass(frozen=True)
class GuestPrincipal:
    guest_id: str


class CookieAuthAdapter(AuthPort):
    """Guest identity via httpOnly cookie. Never trust client-supplied user_id."""

    def set_guest_cookie(self, response: Response, guest_id: str) -> None:
        from src.core.settings import get_settings

        try:
            secure = get_settings().cookie_secure
        except Exception:
            secure = os.environ.get("ENVIRONMENT", "local") != "local"
        response.set_cookie(
            GUEST_COOKIE_NAME,
            guest_id,
            httponly=True,
            samesite="lax",
            secure=secure,
        )

    def issue_guest(self, response: Response) -> GuestPrincipal:
        guest_id = str(uuid4())
        self.set_guest_cookie(response, guest_id)
        return GuestPrincipal(guest_id=guest_id)

    def read_principal(self, request: Request) -> GuestPrincipal | None:
        guest_id = request.cookies.get(GUEST_COOKIE_NAME)
        if not guest_id:
            return None
        return GuestPrincipal(guest_id=guest_id)


# P0 tests and fakes may still construct the stub name.
StubAuthAdapter = CookieAuthAdapter
