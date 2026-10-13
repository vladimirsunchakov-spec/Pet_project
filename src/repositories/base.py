from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from src.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        self.db = db
        self.model = model

    async def get(self, id: UUID) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id, self.model.is_deleted == False)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update(self, id: UUID, values: dict[str, object]) -> Optional[ModelType]:
        stmt = (
            update(self.model)
            .where(self.model.id == id, self.model.is_deleted == False)
            .values(**values)
            .returning(self.model)
        )
        result = await self.db.execute(stmt)
        updated = result.scalar_one_or_none()
        await self.db.flush()
        if updated is not None:
            await self.db.refresh(updated)
        return updated

    async def soft_delete(self, id: UUID) -> Optional[ModelType]:
        stmt = (
            update(self.model)
            .where(self.model.id == id, self.model.is_deleted == False)
            .values(is_deleted=True, deleted_at=datetime.now(timezone.utc))
            .returning(self.model)
        )
        result = await self.db.execute(stmt)
        deleted = result.scalar_one_or_none()
        await self.db.flush()
        if deleted is not None:
            await self.db.refresh(deleted)
        return deleted

    async def get_with_relations(
        self,
        id: UUID,
        relations: list[str],
    ) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id, self.model.is_deleted == False)
        options = [selectinload(getattr(self.model, rel)) for rel in relations]
        query = query.options(*options)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_with_relations(
        self,
        relations: list[str],
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        query = select(self.model).where(self.model.is_deleted == False)
        options = [selectinload(getattr(self.model, rel)) for rel in relations]
        query = query.options(*options).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_for_update(
        self,
        id: UUID,
        relations: list[str] | None = None,
    ) -> Optional[ModelType]:
        query = (
            select(self.model)
            .where(self.model.id == id, self.model.is_deleted == False)
            .with_for_update(skip_locked=True)
        )
        if relations:
            options = [selectinload(getattr(self.model, rel)) for rel in relations]
            query = query.options(*options)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
