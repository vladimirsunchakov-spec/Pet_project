from http import HTTPStatus
from .base import BaseHTTPException

class ValidationError(BaseHTTPException):

    def __init__(self, detail: str):
        super().__init__(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=detail
        )