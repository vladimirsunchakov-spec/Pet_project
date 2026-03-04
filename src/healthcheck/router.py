from src.schemas.healthcheck import HealthCheckResponse

from fastapi import APIRouter

router = APIRouter()


@router.get('/healthcheck', response_model=HealthCheckResponse)
async def healthcheck() -> HealthCheckResponse:
    return HealthCheckResponse(status="ok")