from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
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

    async def get_by_username(self, username: str) -> Optional[UserModel]:
        query = select(UserModel).where(
            UserModel.username == username,
            UserModel.is_deleted == False,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def upsert_user(self, user: UserModel) -> UserModel:
        user_id = user.id or uuid4()
        stmt = (
            pg_insert(UserModel)
            .values(
                id=user_id,
                username=user.username,
                phone=str(user.phone),
            )
            .on_conflict_do_nothing(index_elements=[UserModel.username])
            .returning(UserModel)
        )
        result = await self.db.execute(stmt)
        created = result.scalar_one_or_none()
        if created is None:
            existing = await self.get_by_username(user.username)
            if existing is None:
                raise RuntimeError(f"User '{user.username}' conflicted but was not found")
            return existing

        if user.passport is not None:
            passport = user.passport
            passport.user_id = created.id
            self.db.add(passport)

        await self.db.flush()
        await self.db.refresh(created)
        return created
