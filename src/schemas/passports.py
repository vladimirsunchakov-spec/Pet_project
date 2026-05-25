from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from typing import Optional
from src.exceptions import ValidationError
from src.models.passports import PassportModel

class PassportCreate(BaseModel):
    passport_number: str = Field(min_length=5, max_length=20)
    user_id: UUID

    @field_validator("passport_number")
    @classmethod
    def passport_number_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValidationError("Passport cannot be empty")
        return v

    def to_model(self) -> "PassportModel":
        return PassportModel(passport_number=self.passport_number, user_id=self.user_id)

class PassportUpdate(BaseModel):
    passport_number: Optional[str] = Field(None, min_length=5, max_length=20)

    def update_model(self, passport: PassportModel) -> None:
        update_data = self.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(passport,field, value)

class PassportResponse(BaseModel):
    id: UUID
    passport_number: str

    class Config:
        from_attributes = True