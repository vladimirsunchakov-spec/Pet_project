from typing import Any, Generic, List, Optional, Type, TypeVar
from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

ModelType = TypeVar("ModelType", bound="BaseServiceModel")

class BaseRepository(Generic[ModelType]):
    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        self.db = db
        self.model = model

    async def get(self, id: UUID, **filters:Any) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id, self.model.is_deleted == False)
        for field, value in filters.items():
            query = query.where(getattr(self.model, field) == value)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100, **filters: Any) -> List[ModelType]:
        query = select(self.model).where(self.model.is_deleted == False)
        for field, value in filters.items():
            query = query.where(getattr(self.model, field) == value)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, id: UUID, **values: Any) -> Optional[ModelType]:
        stmt = (
            update(self.model)
            .where(self.model.id == id, self.model.is_deleted == False)
            .values(**values)
            .returning(self.model)
        )
        result = await self.db.execute(stmt)
        updated = result.scalar_one_or_none()
        if updated:
            await self.db.flush()
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
        if deleted:
            await self.db.flush()
            await self.db.refresh(deleted)
        return deleted

    async def delete(self, id: UUID) -> Optional[ModelType]:
        stmt = (
            delete(self.model)
            .where(self.model.id == id, self.model.is_deleted == False)
            .returning(self.model)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_relations(
        self,
        id: UUID,
        relations: Optional[List[str]] = None,
        **filters: Any
    ) -> Optional[ModelType]:

        query = select(self.model).where(self.model.id == id, self.model.is_deleted == False)
        if relations:
            options = [selectinload(getattr(self.model, rel)) for rel in relations]
            query = query.options(*options)
        for field, value in filters.items():
            query = query.where(getattr(self.model, field) == value)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_with_relations(
        self,
        skip: int = 0,
        limit: int = 100,
        relations: Optional[List[str]] = None,
        **filters: Any
    ) -> List[ModelType]:

        query = select(self.model).where(self.model.is_deleted == False)
        if relations:
            options = [selectinload(getattr(self.model, rel)) for rel in relations]
            query = query.options(*options)
        for field, value in filters.items():
            query = query.where(getattr(self.model, field) == value)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_for_update(self, id: UUID, **filters: Any) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id, self.model.is_deleted == False).with_for_update(skip_locked=True)
        for field, value in filters.items():
            query = query.where(getattr(self.model, field) == value)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()