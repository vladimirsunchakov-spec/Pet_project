from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from src.services.base import BaseService
from src.middleware.request_id import get_request_id
from src.exceptions import NotFoundError
from src.models.authors import AuthorModel
from src.models.books import BookModel
from src.schemas.authors import AuthorCreate, AuthorUpdate, AuthorResponse


class AuthorsBooksService(BaseService):
    def __init__(self, db: AsyncSession):
        self.db = db
        self.request_id = get_request_id()

    async def create_author(self, data: AuthorCreate) -> AuthorResponse:
        self._log_info("Creating author", request_id=self.request_id, name=data.name)

        author = AuthorModel.from_schema(data)
        self.db.add(author)
        books = []
        for book_data in data.books:
            book = BookModel.from_schema(book_data)
            books.append(book)
        self.db.add_all(books)
        author.books.extend(books)

        await self.db.refresh(author)

        self._log_info("Author created", entity_id=author.id, request_id=self.request_id)
        return AuthorResponse.model_validate(author)

    async def get_author(self, author_id: UUID) -> AuthorResponse:
        self._log_info("Fetching author", entity_id=author_id, request_id=self.request_id)

        query = select(AuthorModel).where(AuthorModel.id == author_id)
        result = await self.db.execute(query)
        author = result.scalar_one_or_none()

        if not author:
            self._log_warning("Author not found", entity_id=author_id, request_id=self.request_id)
            raise NotFoundError("Author", str(author_id))

        return AuthorResponse.model_validate(author)

    async def update_author(self, author_id: UUID, data: AuthorUpdate) -> AuthorResponse:
        self._log_info("Updating author", entity_id=author_id, request_id=self.request_id)

        author = await self.get_author(author_id)
        author.update_from_schema(data)

        if data.add_books:
            for book_data in data.add_books:
                existing = any(book.title == book_data.title for book in author.books)
                if existing:
                    self._log_warning("Book already exists", entity_id=author_id, request_id=self.request_id)
                    continue
                book = BookModel.from_schema(book_data)
                self.db.add(book)
                author.books.append(book)

        await self.db.refresh(author)

        self._log_info("Author updated", entity_id=author.id, request_id=self.request_id, added_book_count=len(data.add_books) if data.add_books else 0)
        return AuthorResponse.model_validate(author)

    async def delete_author(self, author_id: UUID) -> None:
        self._log_info("Deleting author", entity_id=author_id, request_id=self.request_id)

        author = await self.get_author(author_id=author_id)

        await self.db.delete(author)
        self._log_info("Author deleted", entity_id=author.id, request_id=self.request_id)
