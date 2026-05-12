from http import HTTPStatus

from .base import BaseHTTPException
from fastapi import status

class ValidationError(BaseHTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)