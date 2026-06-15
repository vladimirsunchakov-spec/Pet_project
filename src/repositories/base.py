from typing import Any, Generic, List, Optional, Type, TypeVar
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        self.db = db
        self.model = model

    async def create(self, **kwargs: Any) -> ModelType:
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance


    async def get(self, id: UUID, **filters:Any) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id, self.model.is_deleted == False)
        for field, value in filters.items():
            if value is not None:
                query = query.where(getattr(self.model, field) == value)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100, **filters: Any) -> List[ModelType]:
        query = select(self.model).where(self.model.is_deleted == False)
        for field, value in filters.items():
            if value is not None:
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
        return result.scalar_one_or_none()

    async def soft_delete(self, id: UUID) -> bool:
        stmt = (
            update(self.model)
            .where(self.model.id == id, self.model.is_deleted == False)
            .values(is_deleted=True, deleted_at=datetime.now(timezone.utc))
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0