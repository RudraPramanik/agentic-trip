"""Trip get + GuidebookExport routes (P5)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.modules.chat import SqlSessionRepository
from src.modules.trips import TripAccessError, TripService
from src.modules.trips.repository import SqlTripRepository
from src.ports import AuthPort

router = APIRouter(prefix="/api/v1")


def _trip_service(db: AsyncSession) -> TripService:
    return TripService(SqlSessionRepository(db), SqlTripRepository(db))


@router.get("/trips/{trip_id}")
async def get_trip(
    trip_id: str,
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> dict:
    auth: AuthPort = request.app.state.auth_port
    principal = auth.read_principal(request)
    if principal is None:
        raise HTTPException(status_code=404, detail="trip not found")
    trips = getattr(request.app.state, "trip_service_factory", None)
    service = trips(db) if trips is not None else _trip_service(db)
    try:
        return await service.get_trip(trip_id, principal.guest_id)
    except TripAccessError:
        raise HTTPException(status_code=404, detail="trip not found") from None


@router.get("/trips/{trip_id}/export")
async def export_trip(
    trip_id: str,
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> dict:
    auth: AuthPort = request.app.state.auth_port
    principal = auth.read_principal(request)
    if principal is None:
        raise HTTPException(status_code=404, detail="trip not found")
    trips = getattr(request.app.state, "trip_service_factory", None)
    service = trips(db) if trips is not None else _trip_service(db)
    try:
        export = await service.export_guidebook(trip_id, principal.guest_id)
    except TripAccessError:
        raise HTTPException(status_code=404, detail="trip not found") from None
    return export.to_dict()
