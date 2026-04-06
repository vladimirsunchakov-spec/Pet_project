from src.schemas.base import StatusResponse
from src.core.enums import StatusEnum
from fastapi import APIRouter, status

router = APIRouter()


@router.get('/v1/healthcheck', status_code=status.HTTP_200_OK)
async def healthcheck():
    return {"status": "ok"}