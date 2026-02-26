from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from fastapi import HTTPException, status

from src.models.books import BookModel
from src.schemas.books import BookCreate, BookUpdate, BookResponse

class BookService:
    @staticmethod
    async def create(db: AsyncSession, data: BookCreate) -> BookResponse:
        # Создание книги
        book = BookModel(title=data.title)
        db.add(book)
        await db.commit()
        await db.refresh(book)

        return BookResponse.model_validate(book)

    @staticmethod
    async def get_by_id(db: AsyncSession, book_id: UUID) -> BookResponse:
        # Получение книги по ID
        query = select(BookModel).where(BookModel.id == book_id)
        result = await db.execute(query)
        book = result.scalar_one_or_none()

        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found")

        return BookResponse.model_validate(book)

    @staticmethod
    async def update(db: AsyncSession, book_id: UUID, data: BookUpdate) -> BookResponse:
        # Обновление книги
        await BookService.get_by_id(db, book_id)

        stmt = update(BookModel).where(BookModel.id == book_id).values(title=data.title)
        await db.execute(stmt)
        await db.commit()

        return await BookService.get_by_id(db, book_id)

    @staticmethod
    async def delete(db: AsyncSession, book_id: UUID) -> None:
        # Удаление книги каскадно
        book = await BookService.get_by_id(db, book_id)
        await db.delete(book)
        await db.commit()