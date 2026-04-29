from pydantic import BaseModel, Field
from uuid import UUID
from pydantic_extra_types.phone_numbers import PhoneNumber
from sqlalchemy.testing.pickleable import User


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    phone: PhoneNumber

    def to_model(self):
        from src.models.users import UserModel
        from src.models.passports import PassportModel

        user = UserModel(username=self.username, phone=self.phone)
        if self.passport:
            user.passport = PassportModel(passport_number=self.passport.passport_number, user_id=None)
        return user


class UserUpdate(UserCreate):
    pass

class UserResponse(BaseModel):
    id: UUID
    username: str
    phone: str

    class Config:
        from_attributes = True