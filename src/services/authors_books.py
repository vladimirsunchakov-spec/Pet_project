from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timezone
from src.services.base import BaseService
from src.middleware.request_id import get_request_id
from src.exceptions import NotFoundError, AlreadyExistsError
from src.models.authors import AuthorModel
from src.schemas.authors import AuthorCreate, AuthorUpdate, AuthorResponse
from typing import List

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

        query = (select(AuthorModel)
                 .where(AuthorModel.id == author_id, AuthorModel.is_deleted == False)
                 .options(selectinload(AuthorModel.books)))
        result = await self.db.execute(query)
        author = result.scalar_one_or_none()

        if not author:
            self._log_warning("Author not found", entity_id=author_id, request_id=self.request_id)
            raise NotFoundError("Author", str(author_id))

        return AuthorResponse.model_validate(author)

    async def get_authors(self, skip: int = 0, limit: int = 100) -> List[AuthorResponse]:
        self._log_info("Fetching authors", skip=skip, limit=limit, request_id=self.request_id)
        query = (
            select(AuthorModel)
            .where(AuthorModel.is_deleted == False)
            .offset(skip)
            .limit(limit)
            .options(selectinload(AuthorModel.books))
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(query)
        authors = result.scalars().all()

        return AuthorResponse.from_model_list(authors)

    async def update_author(self, author_id: UUID, data: AuthorUpdate) -> AuthorResponse:
        self._log_info("Updating author", entity_id=author_id, request_id=self.request_id)

        author = await self.get_author(author_id)
        data.update_model(author)

        await self.db.refresh(author)

        self._log_info("Author updated", entity_id=author_id, request_id=self.request_id)
        return AuthorResponse.model_validate(author)

    async def delete_author(self, author_id: UUID) -> None:
        self._log_info("Deleting author", entity_id=author_id, request_id=self.request_id)

        stmt = (update(AuthorModel).where(AuthorModel.id == author_id).values(is_deleted=True, deleted_at=datetime.now(timezone.utc)))
        await self.db.execute(stmt)
        self._log_info("Author deleted", entity_id=author_id, request_id=self.request_id)
