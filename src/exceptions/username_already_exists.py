from .base import BaseHTTPException
from fastapi import status

class UsernameAlreadyExistsError(BaseHTTPException):
    def __init__(self, username:str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=f"Username '{username}' already exists")