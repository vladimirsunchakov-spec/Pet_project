from pydantic import BaseModel
from uuid import UUID

class CityCreate(BaseModel):
    name: str

class CityUpdate(CityCreate):
    pass

class CityResponse(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True