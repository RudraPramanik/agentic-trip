from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.modules.catalog.dto import AcquireEnqueueResponse, AcquireRequest
from src.modules.catalog.facade import DefaultPlacesFacade
from src.modules.catalog.repository import SqlPlaceRepository
from src.modules.catalog.service import CatalogService
from src.modules.chat.repository import SchemaUnavailableError, SqlSessionRepository
from src.modules.chat.service import SessionAccessError

router = APIRouter(prefix="/api/v1")

_SCHEMA_DETAIL = {
    "code": "schema_unavailable",
    "message": "Product schema is not applied",
}


def get_catalog_service(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> CatalogService:
    facade = getattr(request.app.state, "places_facade", None) or DefaultPlacesFacade()
    queue = request.app.state.acquire_queue
    return CatalogService(
        auth=request.app.state.auth_port,
        sessions=SqlSessionRepository(db),
        places=SqlPlaceRepository(db),
        facade=facade,
        queue=queue,
        obs=request.app.state.obs_port,
    )


@router.get("/sessions/{session_id}/catalog")
async def get_catalog_readiness(
    session_id: str,
    request: Request,
    catalog: CatalogService = Depends(get_catalog_service),
) -> dict:
    try:
        readiness = await catalog.readiness(request, session_id)
    except SchemaUnavailableError:
        raise HTTPException(status_code=503, detail=_SCHEMA_DETAIL) from None
    except SessionAccessError:
        raise HTTPException(status_code=404, detail="session not found") from None
    return readiness.model_dump()


@router.post("/catalog/acquire")
async def acquire_catalog(
    body: AcquireRequest,
    request: Request,
    catalog: CatalogService = Depends(get_catalog_service),
) -> dict:
    try:
        result = await catalog.enqueue_acquire(request, body.session_id)
    except SchemaUnavailableError:
        raise HTTPException(status_code=503, detail=_SCHEMA_DETAIL) from None
    except SessionAccessError:
        raise HTTPException(status_code=404, detail="session not found") from None
    return AcquireEnqueueResponse(
        job_id=result.get("job_id"),
        status=str(result.get("status") or "failed"),
    ).model_dump()
