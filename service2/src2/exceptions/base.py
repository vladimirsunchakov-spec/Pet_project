from fastapi import HTTPException
from typing import Optional

class BaseHTTPException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[dict] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)