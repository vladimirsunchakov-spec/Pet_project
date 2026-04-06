from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from src.services.base import BaseService
from src.middleware.request_id import get_request_id
from src.exceptions import NotFoundError
from src.models.authors import AuthorModel
from src.models.books import BookModel
from src.schemas.authors import AuthorCreate, AuthorUpdate


class AuthorsBooksService(BaseService):
    def __init__(self, **kwargs):
        self.db: AsyncSession = kwargs.get("db")
        self.request_id: str = kwargs.get("request_id", get_request_id())

    async def create_author(self, **kwargs) -> AuthorModel:
        data = kwargs.get("data")
        self._log_info("Creating author", request_id=self.request_id, name=data.name)

        author = AuthorModel.from_schema(data)
        self.db.add(author)
        await self.db.flush()

        for book_data in data.books:
            book = BookModel.from_schema(book_data)
            self.db.add(book)
            author.books.append(book)

        await self.db.refresh(author)

        self._log_info("Author created", entity_id=author.id, request_id=self.request_id)
        return author

    async def get_author(self, **kwargs) -> AuthorModel:
        author_id = kwargs.get("author_id")
        self._log_info("Fetching author", entity_id=author_id, request_id=self.request_id)

        query = select(AuthorModel).where(AuthorModel.id == author_id)
        result = await self.db.execute(query)
        author = result.scalar_one_or_none()

        if not author:
            self._log_warning("Author not found", entity_id=author_id, request_id=self.request_id)
            raise NotFoundError ("Author", str(author_id))

        return author

    async def update_author(self, **kwargs) -> AuthorModel:
        data = kwargs.get("data")
        author_id = kwargs.get("author_id")
        self._log_info("Updating author", entity_id=author_id, request_id=self.request_id)

        author = await self.get_author(author_id=author_id)

        author.name = data.name
        author.books = []

        for book_data in data.books:
            book = BookModel.from_schema(book_data)
            self.db.add(book)
            author.books.append(book)

        await self.db.refresh(author)

        self._log_info("Author updated", entity_id=author.id, request_id=self.request_id)
        return author

    async def delete_author(self, **kwargs) -> None:
        author_id = kwargs.get("author_id")

        self._log_info("Deleting author", entity_id=author_id, request_id=self.request_id)

        author = await self.get_author(author_id=author_id)

        await self.db.delete(author)

        self._log_info("Author deleted", entity_id=author.id, request_id=self.request_id)
