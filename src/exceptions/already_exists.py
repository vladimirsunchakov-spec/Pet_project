from fastapi import HTTPException, status
from typing import Optional
from .base import BaseHTTPException

class AlreadyExistsError(BaseHTTPException):
    def __init__(self, field: str, value: str, detail: Optional[str] = None) -> None:
        if detail is None:
            detail = f"{field}' {value}' already exists."
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)