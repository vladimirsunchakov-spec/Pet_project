from pydantic import BaseModel, Field
from uuid import UUID
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Optional
from schemas.passports import PassportCreate, PassportUpdate


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    phone: PhoneNumber
    passport: Optional["PassportCreate"] = None

    def to_model(self):
        from src.models.users import UserModel

        user = UserModel(username=self.username, phone=self.phone)
        if self.passport:
            user.passport = self.passport.to_model()
        return user

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    phone: Optional[str] = Field(None, min_length=3, max_length=50)
    passport: Optional["PassportUpdate"] = None

    def update_model(self, user: "UserModel") -> None:
        if self.username is not None:
            user.username = self.username
        if self.phone is not None:
            user.phone = self.phone

class UserResponse(BaseModel):
    id: UUID
    username: str
    phone: str

    class Config:
        from_attributes = True