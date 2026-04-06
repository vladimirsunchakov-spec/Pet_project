from pydantic import BaseModel, Field
from uuid import UUID


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)

class BookUpdate(BookCreate):
    pass

class BookResponse(BaseModel):
    id: UUID
    title: str

    class Config:
        from_attributes = True