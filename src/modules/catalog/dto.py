from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CatalogReadinessResponse(BaseModel):
    ready: bool
    status: str
    place_count: int | None = None
    job_id: str | None = None
    error: str | None = None


class AcquireRequest(BaseModel):
    session_id: str = Field(min_length=1)


class AcquireEnqueueResponse(BaseModel):
    job_id: str | None = None
    status: str


AcquireStatus = Literal["pending", "running", "ready", "partial", "failed"]
