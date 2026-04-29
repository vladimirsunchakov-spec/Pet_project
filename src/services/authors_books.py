from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from src.services.base import BaseService
from src.middleware.request_id import get_request_id
from src.exceptions import NotFoundError, AlreadyExistsError
from src.models.authors import AuthorModel
from src.models.books import BookModel
from src.schemas.authors import AuthorCreate, AuthorUpdate, AuthorResponse


class AuthorsBooksService(BaseService):
    def __init__(self, db: AsyncSession):
        self.db = db
        self.request_id = get_request_id()

    async def create_author(self, data: AuthorCreate) -> AuthorResponse:
        self._log_info("Creating author", request_id=self.request_id, name=data.name)

        author = data.to_model()
        self.db.add(author)

        await self.db.refresh(author)

        self._log_info("Author created", entity_id=author.id, request_id=self.request_id, books_count=len(data.books))
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
            existing_titles = {book.title for book in author.books}
            for book_data in data.add_books:
                if book_data.title in existing_titles:
                    self._log_warning("Book already exists", entity_id=author_id, request_id=self.request_id)
                    raise AlreadyExistsError("Book", book_data.title)

            new_books = [BookModel.from_schema(book_data) for book_data in data.add_books]
            self.db.add_all(new_books)
            author.books.extend(new_books)

        await self.db.refresh(author)

        self._log_info("Author updated", entity_id=author.id, request_id=self.request_id, added_book_count=len(data.add_books) if data.add_books else 0)
        return AuthorResponse.model_validate(author)

    async def delete_author(self, author_id: UUID) -> None:
        self._log_info("Deleting author", entity_id=author_id, request_id=self.request_id)

        author = await self.get_author(author_id=author_id)

        await self.db.delete(author)
        self._log_info("Author deleted", entity_id=author.id, request_id=self.request_id)
