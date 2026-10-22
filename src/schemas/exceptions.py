from pydantic import BaseModel
from typing import Optional

class ErrorDetails(BaseModel):
    url: Optional[str] = None
    response: Optional[str] = None
    error: Optional[str] = None
    retryable: Optional[bool] = None