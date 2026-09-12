"""Chat feature package — session + dialogue service."""

from src.modules.chat.dto import (
    CreateSessionResponse,
    HitlChoiceRequest,
    SendMessageRequest,
    SessionProjection,
)
from src.modules.chat.models import TripSessionState
from src.modules.chat.repository import (
    InMemorySessionRepository,
    SessionRepository,
    SqlSessionRepository,
)
from src.modules.chat.service import ChatService, HitlStateError, SessionAccessError, SseEvent

__all__ = [
    "ChatService",
    "CreateSessionResponse",
    "HitlChoiceRequest",
    "HitlStateError",
    "InMemorySessionRepository",
    "SendMessageRequest",
    "SessionAccessError",
    "SessionProjection",
    "SessionRepository",
    "SqlSessionRepository",
    "SseEvent",
    "TripSessionState",
]
