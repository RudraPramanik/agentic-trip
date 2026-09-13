"""Trip draft persistence + get/export (P4/P5)."""

from __future__ import annotations

from typing import Any

from src.modules.chat.models import TripSessionState
from src.modules.chat.repository import SessionRepository
from src.modules.planner.caps import ensure_revise_baseline
from src.modules.planner.types import Itinerary, ValidateResult
from src.modules.trips.export import GuidebookExport, to_guidebook_export
from src.modules.trips.models import TripArtifact, new_trip_id
from src.modules.trips.repository import InMemoryTripRepository, TripRepository


class TripPersistError(Exception):
    """Refused to persist (validation fail / abort)."""


class TripAccessError(Exception):
    """Unknown or foreign trip."""


class TripService:
    """Persists guest session drafts and owned trip artifacts. Does not unlock Explore."""

    # Explicit product law: draft ≠ authenticated saved trip (Explore last-trip locked).
    LAST_TRIP_UNLOCKED_BY_DRAFT = False

    def __init__(
        self,
        sessions: SessionRepository,
        trips: TripRepository | None = None,
    ) -> None:
        self._sessions = sessions
        self._trips = trips if trips is not None else InMemoryTripRepository()

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

        trip_id = state.trip_id or new_trip_id()
        state.trip_id = trip_id
        state.itinerary = body
        state.validation = val_dict
        state.budget = "generate"
        ensure_revise_baseline(state)

        artifact = TripArtifact(
            trip_id=trip_id,
            guest_id=state.guest_id,
            session_id=state.session_id,
            status="draft",
            itinerary=body,
            validation=val_dict,
            route_geometry=None,
        )
        await self._trips.save(artifact)
        return await self._sessions.save(state)

    async def get_trip(self, trip_id: str, guest_id: str) -> dict[str, Any]:
        """Return owned trip artifact dict. Backfills from session if needed."""
        trip = await self._trips.get(trip_id)
        if trip is not None:
            if trip.guest_id != guest_id:
                raise TripAccessError("unknown trip")
            return trip.to_dict()

        # Backfill path: trip_id on a session with draft but missing trips row
        # (pre-P5 drafts or partial writes). Scan is avoided — caller uses known id.
        raise TripAccessError("unknown trip")

    async def ensure_trip_for_session(
        self, state: TripSessionState
    ) -> TripSessionState:
        """Assign trip_id + artifact for older drafts missing identity."""
        if not state.itinerary:
            return state
        if state.trip_id:
            existing = await self._trips.get(state.trip_id)
            if existing is not None:
                return state
            # Rehydrate missing artifact
            artifact = TripArtifact(
                trip_id=state.trip_id,
                guest_id=state.guest_id,
                session_id=state.session_id,
                status=str(state.itinerary.get("status") or "draft"),
                itinerary=dict(state.itinerary),
                validation=dict(state.validation) if state.validation else None,
                route_geometry=None,
            )
            await self._trips.save(artifact)
            return state

        trip_id = new_trip_id()
        state.trip_id = trip_id
        artifact = TripArtifact(
            trip_id=trip_id,
            guest_id=state.guest_id,
            session_id=state.session_id,
            status=str(state.itinerary.get("status") or "draft"),
            itinerary=dict(state.itinerary),
            validation=dict(state.validation) if state.validation else None,
            route_geometry=None,
        )
        await self._trips.save(artifact)
        return await self._sessions.save(state)

    async def export_guidebook(
        self, trip_id: str, guest_id: str
    ) -> GuidebookExport:
        trip = await self.get_trip(trip_id, guest_id)
        return to_guidebook_export(trip)
