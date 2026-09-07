from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Optional, List
from src.schemas.passports import PassportCreate, PassportUpdate
from src.models.users import UserModel
from src.models.passports import PassportModel


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    phone: PhoneNumber
    passport: PassportCreate

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValidationError("Username cannot be empty")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValidationError("Phone number is required")
        if not v.startswith("+") or not v[1:].isdigit():
            raise ValidationError("Phone number must be in E.164 format (e.g. +79123456789)")
        return v

    def to_model(self):
        user = UserModel(username=self.username, phone=self.phone)
        user.passport = self.passport.to_model()
        return user

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    phone: Optional[str] = Field(None, min_length=3, max_length=50)
    passport: Optional["PassportUpdate"] = None

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValidationError("Username cannot be empty if provided")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValidationError("Phone number cannot be empty if provided")
            if not v.startswith("+") or not v[1:].isdigit():
                raise ValidationError("Phone number must be in E.164 format (e.g. +79123456789)")
        return v

    @field_validator("passport")
    @classmethod
    def validate_passport(cls, v: Optional[PassportUpdate]) -> Optional[PassportUpdate]:
        if v is not None and (not v.passport_number or not v.passport_number.strip()):
            raise ValidationError("Passport number cannot be empty if provided")
        return v

    def update_model(self, user: UserModel) -> None:
        update_data = self.model_dump(exclude_unset=True, exclude={"passport"})
        for field, value in update_data.items():
            setattr(user, field, value)

        if self.passport:
            user.passport = self.passport.to_model()

class UserResponse(BaseModel):
    id: UUID
    username: str
    phone: str

    @classmethod
    def from_model_list(cls, model_list: List[UserModel]) -> List["UserResponse"]:
        return [cls.model_validate(model) for model in model_list]

    class Config:
        from_attributes = True