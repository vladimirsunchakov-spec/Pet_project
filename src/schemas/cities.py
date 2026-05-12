from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from src.models.cities import CityModel
from src.exceptions import ValidationError

class CityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if v.strip():
            raise ValidationError('City name cannot be empty')
        return v

    def to_model(self, country: "CountryModel") -> "CityModel":
        return CityModel(name=self.name, country=country)

class CityUpdate(BaseModel):
    pass

class CityResponse(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True