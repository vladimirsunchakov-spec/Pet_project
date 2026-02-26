from pydantic import BaseModel
from uuid import UUID
from typing import List


class BookSchema(BaseModel):
    title: str
# для вложения книг, когда создается автор

class AuthorCreate(BaseModel):
    name: str
    books: List[BookSchema]  # вложенный JSON с книгами
# создание автора с вложенным JSON с книгами

class AuthorUpdate(AuthorCreate):
    pass
# обновление автора, те же поля, что и при создании

class AuthorResponse(BaseModel):
    id: UUID
    name: str
    books: List[BookSchema]
# вложенные книги при ответе
    class Config:
        from_attributes = True