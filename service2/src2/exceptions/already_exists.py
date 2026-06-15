from http import HTTPStatus
from .base import BaseHTTPException

class AlreadyExistsError(BaseHTTPException):

    def __init__(self, field: str, value: str):
        super().__init__(
            status_code=HTTPStatus.CONFLICT,
            detail=f"{field} '{value}' already exists"
        )