from pydantic import BaseModel
from uuid import UUID
from typing import List

class CityNestedSchema(BaseModel):
    name: str

class CountryCreate(BaseModel):
    name: str
    continent: str
    cities: List[CityNestedSchema]

class CountryUpdate(CountryCreate):
    pass

class CountryResponse(BaseModel):
    id: UUID
    name: str
    continent: str
    cities: List[CityNestedSchema]

    class Config:
        from_attributes = True