from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models.books import BookModel
from src.models.authors import AuthorModel
from src.repositories.base import BaseRepository
import logging

logger = logging.getLogger(__name__)

class AuthorRepository(BaseRepository[AuthorModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, AuthorModel)

    async def get_with_relations(self, id: UUID, relations: Optional[List[str]] = None) -> Optional[AuthorModel]:
        logger.info(f"Getting author {id} with relations {relations}")
        query = select(AuthorModel).where(
            AuthorModel.id == id,
            AuthorModel.is_deleted == False
        )

        if relations:
            options = [selectinload(getattr(AuthorModel, rel)) for rel in relations]
            query = query.options(*options)

        result = await self.db.execute(query)
        author = result.scalar_one_or_none()
        if author:
            logger.info(f"Author {id} found")
        else:
            logger.warning(f"Author {id} not found")
        return author

    async def get_with_books(self, id: UUID) -> Optional[AuthorModel]:
        return await self.get_with_relations(id, relations=["books"])

    async def get_all_with_relations(
        self,
        skip: int = 0,
        limit: int = 100,
        relations: Optional[List[str]] = None,
        for_update: bool = False
    ) -> List[AuthorModel]:
        logger.info(f"Getting all authors with relations {relations}, skip {skip}, limit {limit}, for_update {for_update}")
        query = select(AuthorModel).where(AuthorModel.is_deleted == False)

        if relations:
            options = [selectinload(getattr(AuthorModel, rel)) for rel in relations]
            query = query.options(*options)

        query = query.offset(skip).limit(limit)

        if for_update:
            query = query.with_for_update(skip_locked=True)

        result = await self.db.execute(query)
        authors = list(result.scalars().all())
        logger.info(f"Retrieved {len(authors)} authors")
        return authors

    async def get_all_with_books(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuthorModel]:
        return await self.get_all_with_relations(skip, limit, relations=["books"])

    async def get_all_with_books_for_update(self, skip: int = 0, limit: int = 100) -> List[AuthorModel]:
        return await self.get_all_with_relations(skip, limit, relations=["books"], for_update=True)