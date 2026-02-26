from pydantic import BaseModel
from uuid import UUID

class UserCreate(BaseModel):
    username: str
    phone: str
# создание пользователя

class UserUpdate(UserCreate):
    pass
# обновление пользователя

class UserResponse(BaseModel):
    id: UUID
    username: str
    phone: str
# получение данных пользователя
    class Config:
        from_attributes = True