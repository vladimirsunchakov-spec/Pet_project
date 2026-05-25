from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import date
from typing import List, Optional
from src.models.authors import AuthorModel
from src.models.books import BookModel
from src.exceptions import ValidationError

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
            raise ValidationError("Author name cannot be empty")
        return v

    @field_validator("books")
    @classmethod
    def books_not_empty(cls, v: List[BookSchema]) -> List[BookSchema]:
        if not v:
            raise ValidationError("At least one book is required")
        return v

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, v: Optional[date]) -> Optional[date]:
        if v is not None:
            if v > date.today():
                raise ValidationError("Birth date cannot be in the future")
            if v < date(1900, 1, 1):
                raise ValidationError("Birth date is too old (year must be >= 1900)")
        return v

    def to_model(self) -> "AuthorModel":
        author = AuthorModel(name=self.name, birth_date=self.birth_date, country=self.country)
        author.books = [book.to_model() for book in self.books]
        return author

class AuthorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    birth_date: Optional[date] = None
    country: Optional[str] = Field(None, max_length=100)
    books: Optional[List[BookSchema]] = Field(None, max_length=100)

    def update_model(self, author: AuthorModel) -> None:
        simple_fields = ["name", "birth_date", "country"]
        update_data = self.model_dump(exclude_unset=True, include=simple_fields)
        for field, value in update_data.items():
            if value is not None:
                setattr(author, field, value)

        if self.books is not None:
            author.books = [book.to_model() for book in self.books]

class AuthorResponse(BaseModel):
    id: UUID
    name: str
    books: List[BookSchema]
    birth_date: Optional[date]
    country: Optional[str]

    @classmethod
    def from_model_list(cls, models: List[AuthorModel]) -> List["AuthorResponse"]:
        return [cls.model_validate(model) for model in models]

    class Config:
        from_attributes = True