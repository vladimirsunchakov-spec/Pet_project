from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID

from src.exceptions import NotFoundError
from src.models.authors import AuthorModel
from src.models.books import BookModel
from src.schemas.authors import AuthorCreate, AuthorUpdate
from src.schemas.books import BookCreate, BookUpdate
from src.schemas.base import StatusResponse

class AuthorsBooksService:
    @staticmethod
    async def create_author(db: AsyncSession, data: AuthorCreate) -> AuthorModel:

        author = AuthorModel.from_schema(data)
        db.add(author)
        await db.flush()

        for book_data in data.books:
            book = BookModel.from_schema(book_data)
            db.add(book)
            author.books.append(book)

        return author

    @staticmethod
    async def get_author(db: AsyncSession, author_id: UUID) -> AuthorModel | None:
        query = select(AuthorModel).where(AuthorModel.id == author_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_author(db: AsyncSession, author_id: UUID, data: AuthorUpdate) -> AuthorModel:
        author = await AuthorsBooksService.get_author(db, author_id)
        if not author:
            raise NotFoundError("Author not found")

        author.name = data.name
        author.books = []

        for book_data in data.books:
            book = BookModel.from_schema(book_data)
            db.add(book)
            author.books.append(book)

        return author

    @staticmethod
    async def delete_author(db: AsyncSession, author_id: UUID) -> StatusResponse:
        author = await AuthorsBooksService.get_author(db, author_id)

        if not author:
            raise NotFoundError("Author not found")

        await db.delete(author)
        return StatusResponse(status="deleted")

    @staticmethod
    async def add_book_to_author(db: AsyncSession, author_id: UUID, data: BookCreate) -> BookModel:
        author = await AuthorsBooksService.get_author(db, author_id)
        if not author:
            raise NotFoundError("Author not found")

        book = BookModel.from_schema(data)
        db.add(book)
        author.books.append(book)

        return book

    @staticmethod
    async def get_book(db: AsyncSession, book_id: UUID) -> BookModel | None:
        query = select(BookModel).where(BookModel.id == book_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_book(db: AsyncSession, book_id: UUID, data: BookUpdate) -> BookModel:
        book = await AuthorsBooksService.get_book(db, book_id)
        if not book:
            raise NotFoundError("Book not found")

        book.title = data.title
        return book

    @staticmethod
    async def delete_book(db: AsyncSession, book_id: UUID) -> StatusResponse:
        book = await AuthorsBooksService.get_book(db, book_id)
        if not book:
            raise NotFoundError("Book not found")

        await db.delete(book)
        return StatusResponse(status="deleted")