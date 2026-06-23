from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models.passports import PassportModel
from src.models.users import UserModel
from src.repositories.base import BaseRepository

class UserRepository(BaseRepository[UserModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, UserModel)

    async def get_with_passport(self, id: UUID) -> Optional[UserModel]:
        query = (
            select(UserModel)
            .where(UserModel.id == id, UserModel.is_deleted == False)
            .options(selectinload(UserModel.passport))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def get_all_with_passport_query(self, skip: int = 0, limit: int = 100) -> Select:
        return(
            select(UserModel)
            .where(UserModel.is_deleted == False)
            .offset(skip)
            .limit(limit)
            .options(selectinload(UserModel.passport))
        )

    async def get_all_with_passport(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        query = self.get_all_with_passport_query(skip, limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
