from http import HTTPStatus
from .base import BaseHTTPException

class NotFoundError(BaseHTTPException):
    def __init__(self, resource_type: str, resource_id: str ):
        super().__init__(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"{resource_type} with id '{resource_id}' not found"
        )