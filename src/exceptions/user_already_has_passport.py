from .base import BaseHTTPException
from fastapi import status

class UserAlreadyHasPassportError(BaseHTTPException):
    def __init__(self, user_id:str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=f"User with id '{user_id}' already has passport")