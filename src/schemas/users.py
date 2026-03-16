from pydantic import BaseModel
from uuid import UUID

class UserCreate(BaseModel):
    username: str
    phone: str

class UserUpdate(UserCreate):
    pass

class UserResponse(BaseModel):
    id: UUID
    username: str
    phone: str

    class Config:
        from_attributes = True