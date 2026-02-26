from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from fastapi import HTTPException, status

from src.models.authors import AuthorModel
from src.models.books import BookModel
from src.schemas.authors import AuthorCreate, AuthorUpdate, AuthorResponse

class AuthorService:
    @staticmethod
    async def create(db: AsyncSession, data: AuthorCreate) -> AuthorResponse:
    # создание автора с вложенными книгами
        author = AuthorModel(name=data.name)
        db.add(author)
        await db.flush()
        # Обрабатываем вложенные книги
        for book_data in data.books:
            # Ищем книгу по названию
            query = select(BookModel).where(BookModel.title == book_data.title)
            result = await db.execute(query)
            book = result.scalar_one_or_none()

            if not book:
                # Создаем новую книгу
                book = BookModel(title=book_data.title)
                db.add(book)
                await db.flush()
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Author not found")

        return AuthorResponse.model_validate(author)

    @staticmethod
    async def update(db: AsyncSession, author_id: UUID, data: AuthorUpdate) -> AuthorResponse:
        # Обновление автора и книг
        # Проверка существование автора
        await AuthorService.get_by_id(db, author_id)

        # Обновление имя автора
        stmt = update(AuthorModel).where(AuthorModel.id == author_id).values(name=data.name)
        await db.execute(stmt)

        # Получаем автора для работы со связями
        query = select(AuthorModel).where(AuthorModel.id == author_id)
        result = await db.execute(query)
        author = result.scalar_one()

        # Очищаем старые связи
        author.books = []

        # Создаем новые связи
        for book_data in data.books:
            query = select(BookModel).where(BookModel.title == book_data.title)
            result = await db.execute(query)
            book = result.scalar_one_or_none()

            if not book:
                book = BookModel(title=book_data.title)
                db.add(book)
                await db.flush()

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

