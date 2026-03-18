from fastapi import HTTPException, status
from typing import Optional

class NotFoundError(HTTPException):
    def __init__(self, resource_type: str, resource_id: Optional[str] = None, detail: Optional[str] = None):
        if detail is None:
            if resource_id:
                detail = f"{resource_type} with id' {resource_id}' not found"
            else:
                detail = f"{resource_type} not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)