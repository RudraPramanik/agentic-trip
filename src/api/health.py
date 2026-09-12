from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.db.session import ping_db

router = APIRouter()


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    db: bool


@router.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/health/ready")
async def ready(db_ok: bool = Depends(ping_db)) -> JSONResponse:
    payload = ReadyResponse(status="ok" if db_ok else "degraded", db=db_ok)
    status_code = 200 if db_ok else 503
    return JSONResponse(content=payload.model_dump(), status_code=status_code)
