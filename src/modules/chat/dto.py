from typing import Any

from pydantic import BaseModel, Field


class CreateSessionResponse(BaseModel):
    session_id: str
    guest: bool = True


class SendMessageRequest(BaseModel):
    text: str = Field(min_length=1)
    user_id: str | None = None  # ignored — never trust client-supplied identity


class HitlChoiceRequest(BaseModel):
    choice_id: str | None = None
    text: str | None = None
    user_id: str | None = None  # ignored — never trust client-supplied identity


class ChatMessage(BaseModel):
    role: str
    content: str


class SessionProjection(BaseModel):
    session_id: str
    messages: list[ChatMessage]
    budget: str
    hitl: dict[str, Any] | None = None
    trip_scope: dict[str, Any] | None = None
