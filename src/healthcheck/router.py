from src.schemas.base import StatusResponse

from fastapi import APIRouter

router = APIRouter()


@router.get('/v1/healthcheck', response_model=StatusResponse)
async def healthcheck() -> StatusResponse:
    return StatusResponse(status="ok")