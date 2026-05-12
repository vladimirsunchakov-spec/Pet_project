from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from typing import List, Optional
from src.models.cities import CityModel
from src.models.countries import CountryModel
from src.exceptions import ValidationError

class CityNestedSchema(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    def to_model(self, country: "CountryModel") -> "CityModel":
        return CityModel(name=self.name, country=country)


class CountryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    continent: str = Field(min_length=1, max_length=50)
    cities: List[CityNestedSchema] = Field(min_length=1, max_length=50)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValidationError("Country name cannot be empty")
        return v

    @field_validator("continent")
    @classmethod
    def continent_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValidationError("Continent cannot be empty")
        return v

    @field_validator("cities")
    @classmethod
    def cities_not_empty(cls, v: List[CityNestedSchema]) -> List[CityNestedSchema]:
        if not v:
            raise ValidationError("At least one city is required")
        return v

    def to_model(self):
        country = CountryModel(name=self.name, continent=self.continent)
        country.cities = [city.to_model(country) for city in self.cities]
        return country

class CountryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    continent: Optional[str] = Field(None, min_length=1, max_length=50)
    add_cities: Optional[List[CityNestedSchema]] = Field(None, max_length=50)

    def update_model(self, country: "CountryModel") -> None:
        if self.name is not None:
            country.name = self.name
        if self.continent is not None:
            country.continent = self.continent

class CountryResponse(BaseModel):
    id: UUID
    name: str
    continent: str
    cities: List[CityNestedSchema]

    class Config:
        from_attributes = True