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


class StubAuthAdapter(AuthPort):
    def issue_guest(self, response: Response) -> GuestPrincipal:
        guest_id = str(uuid4())
        response.set_cookie(
            GUEST_COOKIE_NAME,
            guest_id,
            httponly=True,
            samesite="lax",
            secure=os.environ.get("ENVIRONMENT", "local") != "local",
        )
        return GuestPrincipal(guest_id=guest_id)

    def read_principal(self, request: Request) -> GuestPrincipal | None:
        guest_id = request.cookies.get(GUEST_COOKIE_NAME)
        if not guest_id:
            return None
        return GuestPrincipal(guest_id=guest_id)
