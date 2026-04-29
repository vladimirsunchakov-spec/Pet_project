from pydantic import BaseModel, Field
from uuid import UUID

class PassportCreate(BaseModel):
    passport_number: str = Field(min_length=5, max_length=20)
    user_id: UUID

class PassportUpdate(PassportCreate):
    passport_number: str = Field(min_length=5, max_length=20)

    def update_from_schema(self, passport: "PassportUpdate") -> None:
        if self.passport_number is not None:
            passport.passport_number = self.passport_number

class PassportResponse(BaseModel):
    id: UUID
    passport_number: str

    class Config:
        from_attributes = True