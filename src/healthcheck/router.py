from src.schemas.base import StatusResponse
from fastapi import APIRouter
from http import HTTPStatus

router = APIRouter()


@router.get('/v1/healthcheck', response_model=StatusResponse, status_code=HTTPStatus.OK)
async def healthcheck() -> StatusResponse:
    return StatusResponse(status=HTTPStatus.OK.description.lower())