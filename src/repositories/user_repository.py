from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models.passports import PassportModel
from src.models.users import UserModel
from src.repositories.base import BaseRepository

class UserRepository(BaseRepository[UserModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, UserModel)

    async def upsert_user(self, user: UserModel) -> UserModel:

        existing = await self.get_by_username(user.username)
        if existing:
            for key, value in user.__dict__.items():
                if not key.startswith("_") and value is not None:
                    setattr(existing, key, value)
            return existing

        self.db.add(user)
        return user

    async def get_with_relations(self, id: UUID, relations: Optional[List[str]] = None) -> Optional[UserModel]:
        query = select(UserModel).where(
            UserModel.id == id,
            UserModel.is_deleted == False
        )
        if relations:
            options = [selectinload(getattr(UserModel, rel)) for rel in relations]
            query = query.options(*options)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_with_passport(self, id: UUID) -> Optional[UserModel]:
        return await self.get_with_relations(id, relations=["passport"])

    async def get_by_username(self, username: str) -> Optional[UserModel]:
        query = select(UserModel).where(UserModel.username == username, UserModel.is_deleted == False)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_with_relations(
        self,
        skip: int = 0,
        limit: int = 100,
        relations: Optional[List[str]] = None,
    ) -> List[UserModel]:
        query = select(UserModel).where(UserModel.is_deleted == False)
        if relations:
            options = [selectinload(getattr(UserModel, rel)) for rel in relations]
            query = query.options(*options)
        query = query.offset(skip).limit(limit)
        query = query.with_for_update(skip_locked=True)
        result = await self.db.execute(query)
        users = list(result.scalars().all())
        return users

    async def passport_exists_for_user(
        self,
        passport_number: str,
        user_id: UUID
    ) -> bool:
        query = select(PassportModel).where(
            PassportModel.number == passport_number,
            PassportModel.user_id == user_id,
            PassportModel.is_deleted == False
        )
        result = await self.db.execute(query)
        exists = result.scalar_one_or_none() is not None
        return exists

    async def get_with_passport_for_update(self, id: UUID) -> Optional[UserModel]:
        query = select(UserModel).where(
            UserModel.id == id,
            UserModel.is_deleted == False,
        ).with_for_update(skip_locked=True)

        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if user:
            await self.db.refresh(user, attribute_names=["passport"])
        return user
