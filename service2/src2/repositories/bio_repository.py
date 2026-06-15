from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from service2.src2.repositories.base import BaseRepository
from service2.src2.models.author_bio import AuthorBio

class BioRepository(BaseRepository[AuthorBio]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, AuthorBio)

    async def get_by_author_id(self, author_id: UUID) -> Optional[AuthorBio]:
        query = select(AuthorBio).where(
            AuthorBio.author_id == author_id,
            AuthorBio.is_deleted == False
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_with_pagination(self, skip: int = 0, limit: int = 100) -> List[AuthorBio]:
        query = (
            select(AuthorBio)
            .where(AuthorBio.is_deleted == False)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def upsert_by_author_id(self, author_id: UUID, **values) -> AuthorBio:
        existing = await self.get_by_author_id(author_id)
        if existing:
            for key, value in values.items():
                if value is not None:
                    setattr(existing, key, value)
            return existing
        else:
            bio = AuthorBio(author_id=author_id, **values)
            self.db.add(bio)
            return bio

