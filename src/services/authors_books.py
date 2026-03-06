from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID

from src.exceptions import NotFoundError, ConflictError
from src.models.authors import AuthorModel
from src.models.books import BookModel
from src.schemas.authors import AuthorCreate, AuthorUpdate, AuthorResponse
from src.schemas.books import BookCreate, BookUpdate, BookResponse

class AuthorsBooksService:
    @staticmethod
    async def create_author(db: AsyncSession, data: AuthorCreate) -> AuthorResponse:
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
    async def get_author(db: AsyncSession, author_id: UUID) -> AuthorResponse:
        # Получение автора по ID с вложенными книгами
        query = select(AuthorModel).where(AuthorModel.id == author_id)
        result = await db.execute(query)
        author = result.scalar_one_or_none()

        if not author:
            raise NotFoundError("Author not found")

        return AuthorResponse.model_validate(author)

    @staticmethod
    async def update_author(db: AsyncSession, author_id: UUID, data: AuthorUpdate) -> AuthorResponse:
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
    async def delete_author(db: AsyncSession, author_id: UUID) -> None:
        # Удаление автора каскадно, удаляются связи
        query = select(AuthorModel).where(AuthorModel.id == author_id)
        result = await db.execute(query)
        author = result.scalar_one_or_none()

        if not author:
            raise NotFoundError("Author not found")

        await db.delete(author)
        await db.commit()

    @staticmethod
    async def create_book(db: AsyncSession, data: BookCreate) -> BookResponse:
        # Создание книги
        book = BookModel.from_schema(data)
        db.add(book)
        await db.commit()
        await db.refresh(book)
        return BookResponse.model_validate(book)

    @staticmethod
    async def get_book(db: AsyncSession, book_id: UUID) -> BookResponse:
        # Получение книги по ID
        query = select(BookModel).where(BookModel.id == book_id)
        result = await db.execute(query)
        book = result.scalar_one_or_none()

        if not book:
            raise NotFoundError("Book not found")
        return BookResponse.model_validate(book)

    @staticmethod
    async def update_book(db: AsyncSession, book_id: UUID, data: BookUpdate) -> BookResponse:
        # Обновление книги
        query = select(BookModel).where(BookModel.id == book_id)
        result = await db.execute(query)
        book = result.scalar_one_or_none()

        if not book:
            raise NotFoundError("Book not found")

        book.title = data.title
        await db.commit()
        await db.refresh(book)
        return await BookResponse.model_validate(book)

    @staticmethod
    async def delete_book(db: AsyncSession, book_id: UUID) -> None:
        # Удаление книги каскадно
        query = select(BookModel).where(BookModel.id == book_id)
        result = await db.execute(query)
        book = result.scalar_one_or_none()

        if not book:
            raise NotFoundError("Book not found")

        await db.delete(book)
        await db.commit()