from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID

from src.exceptions import NotFoundError

from src.models.authors import AuthorModel
from src.models.books import BookModel
from src.schemas.authors import AuthorCreate, AuthorUpdate, AuthorResponse

class AuthorService:
    @staticmethod
    async def create(db: AsyncSession, data: AuthorCreate) -> AuthorResponse:
    # создание автора с вложенными книгами
        author = AuthorModel.from_schema(data)
        db.add(author)
        await db.flush()
        # Обрабатываем вложенные книги
        for book_data in data.books:
            # Создаем новую книгу для автора
            book = BookModel(title=book_data.title)
            db.add(book)
            # Связываем книгу с автором
            author.books.append(book)

        await db.commit()
        await db.refresh(author)

        return AuthorResponse.model_validate(author)

    @staticmethod
    async def get_by_id(db: AsyncSession, author_id: UUID) -> AuthorResponse:
        # Получение автора по ID с вложенными книгами
        query = select(AuthorModel).where(AuthorModel.id == author_id)
        result = await db.execute(query)
        author = result.scalar_one_or_none()

        if not author:
            raise NotFoundError("Author not found")


        return AuthorResponse.model_validate(author)

    @staticmethod
    async def update(db: AsyncSession, author_id: UUID, data: AuthorUpdate) -> AuthorResponse:
        query = select(AuthorModel).where(AuthorModel.id == author_id)
        result = await db.execute(query)
        author = result.scalar_one()
        if not author:
            raise NotFoundError("Author not found")
        # Обновляем имя
        author.name = data.name

        author.books = []

        # Создаем новые связи
        for book_data in data.books:
            book = BookModel(title=book_data.title)
            db.add(book)
            author.books.append(book)

        await db.commit()
        await db.refresh(author)

        return AuthorResponse.model_validate(author)

    @staticmethod
    async def delete(db: AsyncSession, author_id: UUID) -> None:
        # Удаление автора каскадно, удаляются связи
        author = await AuthorService.get_by_id(db, author_id)
        await db.delete(author)
        await db.commit()

