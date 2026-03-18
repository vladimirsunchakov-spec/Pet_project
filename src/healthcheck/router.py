from src.schemas.base import StatusResponse
from src.core.enums import StatusEnum
from fastapi import APIRouter

router = APIRouter()


@router.get('/v1/healthcheck', response_model=StatusResponse)
async def healthcheck() -> StatusResponse:
    return StatusResponse(status=StatusEnum.OK)