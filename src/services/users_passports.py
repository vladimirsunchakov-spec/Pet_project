from datetime import datetime, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID

from models.authors import AuthorModel
from schemas.authors import AuthorResponse
from schemas.users import UserResponse
from src.exceptions import NotFoundError
from src.services.base import BaseService
from src.middleware.request_id import get_request_id
from src.models.users import UserModel
from src.schemas.users import UserCreate, UserUpdate



class UsersPassportsService(BaseService):
    def __init__(self, db: AsyncSession):
        self.db = db
        self.request_id = get_request_id()

    async def create_user(self, data: UserCreate) -> UserResponse:
        self._log_info("Creating user", request_id=self.request_id, username=data.username, phone=data.phone)

        user = data.to_model()
        self.db.add(user)

        await self.db.refresh(user)

        self._log_info("Created user", entity_id=user.id,  request_id=self.request_id)
        return UserResponse.model_validate(user)

    async def get_user(self, user_id: UUID) -> UserResponse:
        self._log_info("Fetching user", entity_id=user_id, request_id=self.request_id)

        query = select(UserModel).where(UserModel.id == user_id, UserModel.is_deleted == False)
        result = await self.db.execute(query)
        user =  result.scalar_one_or_none()

        if not user:
            self._log_error("User not found", entity_id=user_id, request_id=self.request_id)
            raise NotFoundError("User", str(user_id))

        return UserResponse.model_validate(user)

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        self._log_info("Fetching users", skip=skip, limit=limit, request_id=self.request_id)
        query = (
            select(UserModel)
            .where(UserModel.is_deleted == False)
            .offset(skip).limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(query)
        users = result.scalars().all()

        return AuthorResponse.from_model_list(users)

    async def update_user(self, user_id: UUID, data:UserUpdate) -> UserResponse:
        self._log_info("Updating user", entity_id=user_id, request_id=self.request_id)

        user = await self.get_user(user_id=user_id)
        data.update_model(user)

        await self.db.refresh(user)

        self._log_info("Updated user", entity_id=user.id, request_id=self.request_id)
        return UserResponse.model_validate(user)

    async def delete_user(self, user_id: UUID) -> None:
        self._log_info("Deleting user", entity_id=user_id, request_id=self.request_id)

        stmt = (update(UserModel).where(UserModel.id == user_id).values(is_deleted=True, deleted_at=datetime.now(timezone.utc)))

        await self.db.execute(stmt)

        self._log_info("Deleted user", entity_id=user_id, request_id=self.request_id)
