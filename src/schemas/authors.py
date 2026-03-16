from pydantic import BaseModel
from uuid import UUID
from datetime import date
from typing import List


class BookSchema(BaseModel):
    title: str

class AuthorCreate(BaseModel):
    name: str
    books: List[BookSchema]
    birth_date: date | None = None
    country: str | None = None

class AuthorUpdate(AuthorCreate):
    pass

class AuthorResponse(BaseModel):
    id: UUID
    name: str
    books: List[BookSchema]
    birth_date: date | None
    country: str | None

    class Config:
        from_attributes = True