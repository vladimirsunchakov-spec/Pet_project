from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from src.core.enums import StatusEnum
from src.services.base import BaseService
from src.core.request_id import get_request_id
from src.exceptions import NotFoundError
from src.models.authors import AuthorModel
from src.models.books import BookModel
from src.schemas.authors import AuthorCreate, AuthorUpdate
from src.schemas.books import BookCreate, BookUpdate
from src.schemas.base import StatusResponse

class AuthorsBooksService(BaseService):
    @classmethod
    async def create_author(cls, db: AsyncSession, data: AuthorCreate, request_id: str | None = None) -> AuthorModel:
        if request_id is None:
            request_id = get_request_id()
        cls._log_info("Creating author", request_id=request_id, name=data.name)

        author = AuthorModel.from_schema(data)
        db.add(author)
        await db.flush()

        for book_data in data.books:
            book = BookModel.from_schema(book_data)
            db.add(book)
            author.books.append(book)
        cls._log_info("Author created",entity_id=author.id, request_id=request_id)

        return author

    @classmethod
    async def get_author(cls, db: AsyncSession, author_id: UUID, request_id: str | None = None) -> AuthorModel | None:
        if request_id is None:
            request_id = get_request_id()
        cls._log_info("Fetching author", entity_id=author_id, request_id=request_id)

        query = select(AuthorModel).where(AuthorModel.id == author_id)
        result = await db.execute(query)
        author = result.scalar_one_or_none()

        if not author:
            cls._log_warning("Author not found", entity_id=author_id, request_id=request_id)

        return author

    @classmethod
    async def update_author(cls, db: AsyncSession, author_id: UUID, data: AuthorUpdate, request_id: str | None = None) -> AuthorModel:
        if request_id is None:
            request_id = get_request_id()
        cls._log_info("Updating author", entity_id=author_id, request_id=request_id)

        author = await cls.get_author(db, author_id, request_id=request_id)
        if not author:
            cls._log_error("Author not found for update", entity_id=author_id, request_id=request_id)
            raise NotFoundError("Author", str(author_id))

        author.name = data.name
        author.books = []

        for book_data in data.books:
            book = BookModel.from_schema(book_data)
            db.add(book)
            author.books.append(book)

        cls._log_info("Author updated", entity_id=author.id, request_id=request_id)

        return author

    @classmethod
    async def delete_author(cls, db: AsyncSession, author_id: UUID, request_id: str | None = None) -> StatusResponse:
        if request_id is None:
            request_id = get_request_id()
        cls._log_info("Deleting author", entity_id=author_id, request_id=request_id)

        author = await cls.get_author(db, author_id, request_id=request_id)
        if not author:
            cls._log_error("Author not found for delete", entity_id=author_id, request_id=request_id)
            raise NotFoundError("Author", str(author_id))

        await db.delete(author)

        cls._log_info("Author deleted", entity_id=author.id, request_id=request_id)

        return StatusResponse(status=StatusEnum.DELETED)

    @classmethod
    async def add_book_to_author(cls, db: AsyncSession, author_id: UUID, data: BookCreate, request_id: str | None = None) -> BookModel:
        if request_id is None:
            request_id = get_request_id()
        cls._log_info("Adding book to author", entity_id=author_id, request_id=request_id, title=data.title)
        author = await cls.get_author(db, author_id, request_id=request_id)
        if not author:
            cls._log_error("Author not found for add", entity_id=author_id, request_id=request_id)
            raise NotFoundError("Author", str(author_id))

        book = BookModel.from_schema(data)
        db.add(book)
        author.books.append(book)

        cls._log_info("Book added", entity_id=author.id, request_id=request_id, book_id=str(book.id))

        return book

    @classmethod
    async def get_book(cls, db: AsyncSession, book_id: UUID, request_id: str | None = None) -> BookModel | None:
        if request_id is None:
            request_id = get_request_id()
        cls._log_info("Fetching book", entity_id=book_id, request_id=request_id)

        query = select(BookModel).where(BookModel.id == book_id)
        result = await db.execute(query)
        book = result.scalar_one_or_none()

        if not book:
            cls._log_warning("Book not found", entity_id=book_id, request_id=request_id)
        return book

    @classmethod
    async def update_book(cls, db: AsyncSession, book_id: UUID, data: BookUpdate, request_id: str | None = None) -> BookModel:
        if request_id is None:
            request_id = get_request_id()
        cls._log_info("Updating book", entity_id=book_id, request_id=request_id)

        book = await cls.get_book(db, book_id, request_id=request_id)
        if not book:
            cls._log_error("Book not found for update", entity_id=book_id, request_id=request_id)
            raise NotFoundError("Book", str(book_id))

        book.title = data.title
        cls._log_info("Book updated", entity_id=book_id, request_id=request_id)
        return book

    @classmethod
    async def delete_book(cls, db: AsyncSession, book_id: UUID, request_id: str | None = None) -> StatusResponse:
        if request_id is None:
            request_id = get_request_id()

        cls._log_info("Deleting book", entity_id=book_id, request_id=request_id)

        book = await cls.get_book(db, book_id, request_id=request_id)
        if not book:
            cls._log_error("Book not found for deletion", entity_id=book_id, request_id=request_id)
            raise NotFoundError("Book", str(book_id))

        await db.delete(book)
        cls._log_info("Book deleted", entity_id=book_id, request_id=request_id)
        return StatusResponse(status=StatusEnum.DELETED)