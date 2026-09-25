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

    async def create_user(self, user: UserModel) -> UserModel:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_with_passport(self, user_id: UUID) -> Optional[UserModel]:
        return await self.get_with_relations(user_id, relations=["passport"])

    async def get_by_username(self, username: str) -> Optional[UserModel]:
        query = select(UserModel).where(
            UserModel.username == username,
            UserModel.is_deleted == False,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def upsert_user(self, user: UserModel) -> UserModel:
        existing = await self.get_by_username(user.username)
        if existing:
            for key, value in user.__dict__.items():
                if not key.startswith("_") and value is not None:
                    setattr(existing, key, value)
            return existing

        self.db.add(user)
        return user

    async def get_with_passport_for_update(self, user_id: UUID) -> Optional[UserModel]:
        query = (select(UserModel).where(
            UserModel.id == user_id,
            UserModel.is_deleted == False,
        )
        .options(selectinload(UserModel.passport))
        .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
