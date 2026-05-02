from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional

class PassportCreate(BaseModel):
    passport_number: str = Field(min_length=5, max_length=20)
    user_id: UUID

    def to_model(self) -> "PassportModel":
        from src.models.passports import PassportModel
        return PassportModel(passport_number=self.passport_number, user_id=self.user_id)

class PassportUpdate(BaseModel):
    passport_number: Optional[str] = Field(None, min_length=5, max_length=20)

    def update_model(self, passport: "PassportModel") -> None:
        if self.passport_number is not None:
            passport.passport_number = self.passport_number

class PassportResponse(BaseModel):
    id: UUID
    passport_number: str

    class Config:
        from_attributes = True