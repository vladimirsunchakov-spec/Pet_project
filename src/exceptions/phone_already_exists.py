from .base import BaseHTTPException
from fastapi import status

class PhoneAlreadyExistsError(BaseHTTPException):
    def __init__(self, phone:str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=f"Phone '{phone}' already exists ")