from fastapi import HTTPException, status
from typing import Optional

class ConflictError(HTTPException):
    def __init__(self, resource_type: Optional[str] = None, value: Optional[str] = None, detail: Optional[str] = None):
        if detail is None and resource_type and value:
            detail = f"{resource_type} '{value}' already exists"
        elif detail is None:
            detail = "Conflict"
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)