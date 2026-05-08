from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Optional
from schemas.passports import PassportCreate, PassportUpdate
from src.models.users import UserModel
from src.models.passports import PassportModel
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    phone: PhoneNumber
    passport: Optional["PassportCreate"] = None

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Username cannot be empty")
        return v

    def to_model(self):
        user = UserModel(username=self.username, phone=self.phone)
        if self.passport:
            user.passport = self.passport.to_model()
        return user

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    phone: Optional[str] = Field(None, min_length=3, max_length=50)
    passport: Optional["PassportUpdate"] = None

    def update_model(self, user: "UserModel") -> None:
        update_data = self.model_dump(exclude_unset=True, exclude={"passport"})
        for field, value in update_data.items():
            if value is not None:
                setattr(user, field, value)

        if self.passport is not None:
            if user.passport is None:
                passport_data = self.passport.model_dump(exclude_unset=True)
                user.passport = PassportModel(**passport_data, user_id=user.id)
            else:
                self.passport.update_model(user.passport)

class UserResponse(BaseModel):
    id: UUID
    username: str
    phone: str

    class Config:
        from_attributes = True