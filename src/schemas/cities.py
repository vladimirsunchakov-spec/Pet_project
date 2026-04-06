from pydantic import BaseModel, Field
from uuid import UUID

class CityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)

class CityUpdate(CityCreate):
    pass

class CityResponse(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True