from .base import BaseHTTPException

class RequestIdNotSetError(BaseHTTPException):
    def __init__(self):
        super().__init__(status_code=500, detail="Request Id not set in context.")