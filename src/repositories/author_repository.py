from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models.authors import AuthorModel
from src.repositories.base import BaseRepository
import logging

logger = logging.getLogger(__name__)

class AuthorRepository(BaseRepository[AuthorModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, AuthorModel)

    async def get_with_books(self, id: UUID, request_id: Optional[str] = None) -> Optional[AuthorModel]:
        logger.info(f"Getting author {id} with books | request_id={request_id}")
        query = (
            select(AuthorModel)
            .where(AuthorModel.id == id, AuthorModel.is_deleted == False)
            .options(selectinload(AuthorModel.books))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def get_all_with_books_query(self, skip: int = 0, limit: int = 100) -> Select:
        return (
            select(AuthorModel)
            .where(AuthorModel.is_deleted == False)
            .offset(skip)
            .limit(limit)
            .options(selectinload(AuthorModel.books))
        )

    async def get_all_with_books(self, skip: int = 0, limit: int = 100, request_id: Optional [str] = None) -> List[AuthorModel]:
        logger.info(f"Getting all author with books (skip={skip}, limit={limit}) | request_id={request_id}")

        query = self.get_all_with_books_query(skip, limit)
        result = await self.db.execute(query)
        authors = list(result.scalars().all())
        logger.info(f"Retrieved {len(authors)} authors | request_id={request_id}")
        return authors

    async def get_all_with_books_for_update(self, skip: int = 0, limit: int = 100, request_id: Optional [str] = None) -> List[AuthorModel]:
        logger.info(f"Getting all author with books for update (skip={skip}, limit={limit}) | request_id={request_id}")
        query = (
            select(AuthorModel)
            .where(AuthorModel.is_deleted == False)
            .offset(skip)
            .limit(limit)
            .options(selectinload(AuthorModel.books))
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(query)
        authors = list(result.scalars().all())
        logger.info(f"Retrieved {len(authors)} authors with books (locked) | request_id={request_id}")
        return authors