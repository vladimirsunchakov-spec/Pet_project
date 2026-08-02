from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models.books import BookModel
from src.models.authors import AuthorModel
from src.repositories.base import BaseRepository


class AuthorRepository(BaseRepository[AuthorModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, AuthorModel)

    async def create_author(self, author: AuthorModel) -> AuthorModel:
        self.db.add(author)
        await self.db.flush()
        await self.db.refresh(author)
        return author

    async def update_author(self, author: AuthorModel) -> AuthorModel:
        await self.db.flush()
        await self.db.refresh(author)
        return author

    async def delete_author(self, author_id: UUID) -> bool:
        return await self.soft_delete(author_id)

    async def get_with_relations(self, id: UUID, relations: Optional[List[str]] = None) -> Optional[AuthorModel]:
        query = select(AuthorModel).where(
            AuthorModel.id == id,
            AuthorModel.is_deleted == False
        )

        if relations:
            options = [selectinload(getattr(AuthorModel, rel)) for rel in relations]
            query = query.options(*options)

        result = await self.db.execute(query)
        author = result.scalar_one_or_none()
        return author

    async def get_with_books(self, id: UUID) -> Optional[AuthorModel]:
        return await self.get_with_relations(id, relations=["books"])

    async def get_all_with_relations(
        self,
        skip: int = 0,
        limit: int = 100,
        relations: Optional[List[str]] = None,
    ) -> List[AuthorModel]:
        query = select(AuthorModel).where(AuthorModel.is_deleted == False)
        if relations:
            options = [selectinload(getattr(AuthorModel, rel)) for rel in relations]
            query = query.options(*options)
        query = query.offset(skip).limit(limit)
        query = query.with_for_update(skip_locked=True)
        result = await self.db.execute(query)
        authors = list(result.scalars().all())
        return authors
