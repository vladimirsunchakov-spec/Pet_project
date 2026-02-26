from pydantic import BaseModel
from uuid import UUID

class CityCreate(BaseModel):
    name: str
# создание города

class CityUpdate(CityCreate):
    pass
# обновление города

class CityResponse(BaseModel):
    id: UUID
    name: str
# ответ с данными города

    class Config:
        from_attributes = True