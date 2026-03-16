from pydantic import BaseModel
from uuid import UUID

class PassportCreate(BaseModel):
    passport_number: str
    user_id: UUID

class PassportUpdate(PassportCreate):
    pass

class PassportResponse(BaseModel):
    id: UUID
    passport_number: str

    class Config:
        from_attributes = True