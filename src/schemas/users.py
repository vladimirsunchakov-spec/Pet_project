from pydantic import BaseModel, Field
from uuid import UUID
from pydantic_extra_types.phone_numbers import PhoneNumber

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    phone: PhoneNumber

class UserUpdate(UserCreate):
    pass

class UserResponse(BaseModel):
    id: UUID
    username: str
    phone: str

    class Config:
        from_attributes = True