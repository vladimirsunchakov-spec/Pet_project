from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from src.models.books import BookModel

class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v

    def to_model(self) -> "BookModel":
        return BookModel(title=self.title)

class BookUpdate(BaseModel):
    pass

class BookResponse(BaseModel):
    id: UUID
    title: str

    class Config:
        from_attributes = True