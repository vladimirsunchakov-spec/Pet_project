from pydantic import BaseModel
from uuid import UUID

class CityNestedSchema(BaseModel):
    name: str
# схема для городов при создании страны

class CountryCreate(BaseModel):
    name: str
    continent: str
    cities: list[CityNestedSchema]
# схема для страны с городами

class CountryUpdate(CountryCreate):
    pass
# обновление страны

class CountryResponse(BaseModel):
    id: UUID
    name: str
    continent: str
    cities: list[CityNestedSchema]
 # ответ с данными страны
    class Config:
        from_attributes = True