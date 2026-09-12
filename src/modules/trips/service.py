"""Trip draft persistence — status=draft only; never saved trip."""

from __future__ import annotations

from typing import Any

from src.modules.chat.models import TripSessionState
from src.modules.chat.repository import SessionRepository
from src.modules.planner.types import Itinerary, ValidateResult


class TripPersistError(Exception):
    """Refused to persist (validation fail / abort)."""


class TripService:
    """Persists guest session drafts. Does not unlock last-trip Explore."""

    # Explicit product law: draft ≠ authenticated saved trip (Explore last-trip locked).
    LAST_TRIP_UNLOCKED_BY_DRAFT = False

    def __init__(self, sessions: SessionRepository) -> None:
        self._sessions = sessions

    async def persist_draft(
        self,
        session_id: str,
        itinerary: Itinerary | dict[str, Any],
        validation: ValidateResult | dict[str, Any],
        *,
        aborted: bool = False,
    ) -> TripSessionState:
        if aborted:
            raise TripPersistError("aborted")

        if isinstance(validation, ValidateResult):
            val_ok = validation.ok
            val_dict = validation.to_dict()
        else:
            val_ok = bool(validation.get("ok"))
            val_dict = dict(validation)

        if not val_ok:
            raise TripPersistError("validation_failed")

        if isinstance(itinerary, Itinerary):
            itin = itinerary
        else:
            itin = Itinerary.from_dict(itinerary)
        itin.status = "draft"
        body = itin.to_dict()
        body["status"] = "draft"
        # Explore last-trip must stay locked for guest drafts
        body["saved"] = False
        body["unlocks_last_trip"] = False

        state = await self._sessions.get(session_id)
        if state is None:
            raise TripPersistError("session_not_found")

        state.itinerary = body
        state.validation = val_dict
        state.budget = "generate"
        return await self._sessions.save(state)
