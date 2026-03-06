from pydantic import BaseModel
from uuid import UUID

class PassportCreate(BaseModel):
    passport_number: str
    user_id: UUID
# создание паспорта

class PassportUpdate(PassportCreate):
    pass
# обновление паспорта

class PassportResponse(BaseModel):
    id: UUID
    passport_number: str
# ответ с данными паспорта
    class Config:
        from_attributes = True