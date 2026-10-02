from src.schemas.exceptions import ErrorDetails
from typing import Optional

class ExternalServiceError(Exception):
    def __init__(self, message: str, status_code: int = 500, details: Optional[ErrorDetails] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or ErrorDetails()
        super().__init__(message)

class ExternalServiceUnavailableError(ExternalServiceError):
    pass

class BioResponseParseError(ExternalServiceError):
    pass