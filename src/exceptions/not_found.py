from .base import BaseHTTPException
from fastapi import status

class NotFoundError(BaseHTTPException):
    def __init__(self, resource_type: str, resource_id: str):
        detail = f"{resource_type} with id '{resource_id}' not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
