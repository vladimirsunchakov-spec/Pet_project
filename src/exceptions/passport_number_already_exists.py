from .base import BaseHTTPException
from fastapi import status

class PassportAlreadyExistsError(BaseHTTPException):
    def __init__(self, passport_number:str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=f"Passport number'{passport_number}' already exists")