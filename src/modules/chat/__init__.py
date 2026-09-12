"""Chat feature package — session + dialogue service."""

from src.modules.chat.dto import CreateSessionResponse, SendMessageRequest, SessionProjection
from src.modules.chat.models import TripSessionState
from src.modules.chat.repository import (
    InMemorySessionRepository,
    SessionRepository,
    SqlSessionRepository,
)
from src.modules.chat.service import ChatService, SessionAccessError, SseEvent

__all__ = [
    "ChatService",
    "CreateSessionResponse",
    "InMemorySessionRepository",
    "SendMessageRequest",
    "SessionAccessError",
    "SessionProjection",
    "SessionRepository",
    "SqlSessionRepository",
    "SseEvent",
    "TripSessionState",
]
