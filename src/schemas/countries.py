from pydantic import BaseModel, Field
from uuid import UUID
from typing import List

class CityNestedSchema(BaseModel):
    name: str = Field(min_length=1, max_length=50)

class CountryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    continent: str = Field(min_length=1, max_length=50)
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