from pydantic import BaseModel, Field
from uuid import UUID
from typing import List

class CityNestedSchema(BaseModel):
    name: str = Field(min_length=1, max_length=50)

    def to_model(self, country: "CountryModel") -> "CityModel":
        from src.models.cities import CityModel
        return CityModel(name=self.name, country=country)


class CountryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    continent: str = Field(min_length=1, max_length=50)
    cities: List[CityNestedSchema]

    def to_model(self):
        from src.models.countries import CountryModel
        from src.models.cities import CityModel

        country = CountryModel(name=self.name, continent=self.continent)
        country.cities = [CityModel(name=city.name) for city in self.cities]
        return country

class CountryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    continent: str | None = Field(None, min_length=1, max_length=50)
    add_cities: List[CityNestedSchema] | None = Field(None, min_length=1, max_length=50)

class CountryResponse(BaseModel):
    id: UUID
    name: str
    continent: str
    cities: List[CityNestedSchema]

    class Config:
        from_attributes = True