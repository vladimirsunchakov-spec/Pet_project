from pydantic import BaseModel
from uuid import UUID


class BookCreate(BaseModel):
    title: str
# создание книги без автора

class BookUpdate(BookCreate):
    pass
# обновление книги

class BookResponse(BaseModel):
    id: UUID
    title: str
# ответ с данными книги

    class Config:
        from_attributes = True