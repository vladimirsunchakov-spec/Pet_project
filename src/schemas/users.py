from pydantic import BaseModel, Field
from uuid import UUID
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Optional
from schemas.passports import PassportCreate


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    phone: PhoneNumber
    passport: Optional["PassportCreate"] = None

    def to_model(self):
        from src.models.users import UserModel
        from src.models.passports import PassportModel

        user = UserModel(username=self.username, phone=self.phone)
        if self.passport:
            user.passport = PassportModel(passport_number=self.passport.passport_number, user_id=None)
        return user


class UserUpdate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    phone: str = Field(min_length=3, max_length=50)
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