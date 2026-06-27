from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models.passports import PassportModel
from src.models.users import UserModel
from src.repositories.base import BaseRepository
import logging

logger = logging.getLogger(__name__)

class UserRepository(BaseRepository[UserModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, UserModel)

    async def get_with_relations(self, id: UUID, relations: Optional[List[str]] = None) -> Optional[UserModel]:
        logger.info(f"Getting user: {id} with relations {relations}")
        query = select(UserModel).where(
            UserModel.id == id,
            UserModel.is_deleted == False
        )
        if relations:
            options = [selectinload(getattr(UserModel, rel)) for rel in relations]
            query = query.options(*options)

        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if user:
            logger.info(f"User {id} found")
        else:
            logger.warning(f"User {id} not found")
        return user

    async def get_with_passport(self, id: UUID) -> Optional[UserModel]:
        return await self.get_with_relations(id, relations=["passport"])

    async def get_by_username(self, username: str) -> Optional[UserModel]:
        logger.info(f"Getting user by username: {username}")
        query = select(UserModel).where(UserModel.username == username, UserModel.is_deleted == False)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if user:
            logger.info(f"User with username {username} found")
        else:
            logger.info(f"User with username {username} not found")
        return user

    async def get_all_with_relations(
        self,
        skip: int = 0,
        limit: int = 100,
        relations: Optional[List[str]] = None,
        for_update: bool = False
    ) -> List[UserModel]:
        logger.info(f"Getting all users with relations {relations}, skip={skip}, limit={limit}, for_update={for_update}")
        query = select(UserModel).where(UserModel.is_deleted == False)

        if relations:
            options = [selectinload(getattr(UserModel, rel)) for rel in relations]
            query = query.options(*options)

        query = query.offset(skip).limit(limit)

        if for_update:
            query = query.with_for_update(skip_locked=True)

        result = await self.db.execute(query)
        users = list(result.scalars().all())
        logger.info(f"Retrieved {len(users)} users")
        return users

    async def get_all_with_passport(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        return await self.get_all_with_relations(skip, limit, relations=["passport"])

    async def get_all_with_passport_for_update(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        return await self.get_all_with_relations(skip, limit, relations=["passport"], for_update=True)

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
        logger.info(f"Passport '{passport_number}' exists for user {user_id}: {exists}")

        return exists
