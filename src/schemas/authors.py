from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import date
from typing import List, Optional
from src.models.authors import AuthorModel
from src.models.books import BookModel


class BookSchema(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    def to_model(self) -> "BookModel":
        return BookModel(title=self.title)

class AuthorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    books: List[BookSchema] = Field(min_length=1, max_length=100)
    birth_date: Optional[date] = None
    country: Optional[str] = Field(None, min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Author name cannot be empty")
        return v

    @field_validator("books")
    @classmethod
    def books_not_empty(cls, v: List[BookSchema]) -> List[BookSchema]:
        if not v:
            raise ValueError("At least one book is required")
        return v

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, v: Optional[date]) -> Optional[date]:
        if v is not None:
            if v > date.today():
                raise ValueError("Birth date cannot be in the future")
            if v < date(1900, 1, 1):
                raise ValueError("Birth date is too old (year must be >= 1900)")
        return v

    def to_model(self) -> "AuthorModel":
        author = AuthorModel(name=self.name, birth_date=self.birth_date, country=self.country)
        author.books = [book.to_model() for book in self.books]
        return author

class AuthorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    birth_date: Optional[date] = None
    country: Optional[str] = Field(None, max_length=100)
    add_books: Optional[List[BookSchema]] = Field(None, max_length=100)

    def update_model(self, author: "AuthorModel") -> None:
        update_data = self.model_dump(exclude_unset=True, exclude={"add_books"})
        for field, value in update_data.items():
            if value is not None:
                setattr(author, field, value)
        if self.add_books:
            new_books = [book.to_model() for book in self.add_books]
            if author.books is None:
                author.books = []
            author.books.extend(new_books)

class AuthorResponse(BaseModel):
    id: UUID
    name: str
    books: List[BookSchema]
    birth_date: Optional[date]
    country: Optional[str]

    class Config:
        from_attributes = True