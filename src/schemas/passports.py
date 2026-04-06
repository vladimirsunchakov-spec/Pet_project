from pydantic import BaseModel, Field
from uuid import UUID

class PassportCreate(BaseModel):
    passport_number: str = Field(min_length=5, max_length=20)
    user_id: UUID

class PassportUpdate(PassportCreate):
    pass

class PassportResponse(BaseModel):
    id: UUID
    passport_number: str

    class Config:
        from_attributes = True