from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date
from typing import List


class BookSchema(BaseModel):
    title: str = Field(min_length=1, max_length=100)

class AuthorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    books: List[BookSchema] = Field(min_length=1, max_length=100)
    birth_date: date | None = Field(None, description="birth_date")
    country: str | None = Field(None, max_length=100)

    def to_model(self):
        from src.models.authors import AuthorModel
        from src.models.books import BookModel
        author = AuthorModel(name=self.name, birth_date=self.birth_date, country=self.country)
        author.books = [BookModel(title=book.title) for book in self.books]
        return author

class AuthorUpdate(AuthorCreate):
    name: str | None = Field(None, min_length=1, max_length=100)
    birth_date: date | None = Field(None, description="birth_date")
    country: str | None = Field(None, max_length=100)
    add_books: List[BookSchema] | None = Field(None, min_length=1, max_length=100)

class AuthorResponse(BaseModel):
    id: UUID
    name: str
    books: List[BookSchema]
    birth_date: date | None
    country: str | None

    class Config:
        from_attributes = True