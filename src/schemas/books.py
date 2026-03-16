from pydantic import BaseModel
from uuid import UUID


class BookCreate(BaseModel):
    title: str

class BookUpdate(BookCreate):
    pass

class BookResponse(BaseModel):
    id: UUID
    title: str

    class Config:
        from_attributes = True