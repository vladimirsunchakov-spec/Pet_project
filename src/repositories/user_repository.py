from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.testing.pickleable import User
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

    async def get_with_passport(self, id: UUID) -> Optional[UserModel]:
        return await self.get_with_relations(id, relations=["passport"])

    async def get_by_username(self, username: str) -> Optional[UserModel]:
        return await self.get(User, username=username)

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

    async def upsert_user(self, user: UserModel) -> UserModel:
        existing = await self.get_by_username(user.username)
        if existing:
            for key, value in user.__dict__.items():
                if not key.startswith("__") and value is not None:
                    setattr(existing, key, value)
            return existing

        self.db.add(user)
        return user

    async def get_with_passport_for_update(self, user_id: UUID) -> Optional[UserModel]:
        return await self.get_for_update(user_id, relations=["passport"])
