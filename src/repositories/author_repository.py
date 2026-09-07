from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.authors import AuthorModel
from src.repositories.base import BaseRepository
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

class AuthorRepository(BaseRepository[AuthorModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, AuthorModel)

    async def create_author(self, author: AuthorModel) -> AuthorModel:
        self.db.add(author)
        await self.db.flush()
        await self.db.refresh(author)
        return author

    async def get_with_books(self, id: UUID) -> Optional[AuthorModel]:
        return await self.get_with_relations(id, relations=["books"])

    async def restore(self, author_id: UUID) -> Optional[AuthorModel]:
        stmt = (
            update(self.model)
            .where(
                self.model.id == author_id,
                self.model.is_deleted == True
            )
            .values(
                is_deleted=False,
                deleted_at=None
            )
            .returning(self.model)
        )
        result = await self.db.execute(stmt)
        restored = result.scalar_one_or_none()
        if restored:
            await self.db.flush()
            await self.db.refresh(restored)
        return restored


