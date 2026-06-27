from datetime import datetime, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from uuid import UUID
from src.models.authors import AuthorModel
from src.schemas.authors import AuthorResponse
from src.exceptions import NotFoundError, AlreadyExistsError
from src.services.base import BaseService
from src.middleware.request_id import get_request_id
from src.models.users import UserModel
from src.schemas.users import UserCreate, UserUpdate, UserResponse
from src.core.redis import redis_client
from src.repositories.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)

class UsersPassportsService(BaseService):
    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db
        self.request_id = get_request_id()
        self.user_repo = UserRepository(db)

    async def create_user(self, data: UserCreate) -> UserResponse:
        self._log_info("Creating user", request_id=self.request_id, username=data.username, has_passport=bool(data.passport))

        existing_user = await self.user_repo.get_by_username(data.username)
        if existing_user:
            self._log_error(f"User with username '{data.username}' already exists", request_id=self.request_id)
            raise AlreadyExistsError("User", f"username '{data.username}' already exists")

        user = data.to_model()
        self.db.add(user)
        await self.db.refresh(user)

        self._log_info("Created user", entity_id=user.id, request_id=self.request_id)

        return UserResponse.model_validate(user)

    async def get_user(self, user_id: UUID) -> UserResponse:
        self._log_info("Fetching user", entity_id=user_id, request_id=self.request_id)

        cache_key = f"user:{user_id}"

        try:
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                self._log_info("Cache HIT for user", entity_id=user_id, request_id=self.request_id)
                return UserResponse.model_validate_json(cached_data)

            self._log_info("Cache MISS for user", entity_id=user_id, request_id=self.request_id)
        except Exception as e:
            self._log_warning(f"Redis error on get: {e}", request_id=self.request_id)
        user = await self.user_repo.get_with_passport(user_id)
        if not user:
            self._log_warning("User not found", user_id=user_id, request_id=self.request_id)
            raise NotFoundError("User", str(user_id))
        response = UserResponse.model_validate(user)

        try:
            await redis_client.set(cache_key, response.model_dump(), ttl=3600)
            self._log_info("User cached", user_id=user_id, request_id=self.request_id)
        except Exception as e:
            self._log_warning(f"Redis error on set: {e}", request_id=self.request_id)

        return response

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        self._log_info("Fetching users list", skip=skip, limit=limit, request_id=self.request_id)

        users = await self.user_repo.get_all_with_passport_for_update(skip, limit)

        self._log_info("Users fetched", count=len(users), request_id=self.request_id)
        return UserResponse.from_model_list(users)

    async def update_user(self, user_id: UUID, data: UserUpdate) -> UserResponse:
        self._log_info("Updating user", entity_id=user_id, request_id=self.request_id)

        user = await self.user_repo.get_with_passport(user_id)
        if not user:
            self._log_warning("User not found for update", entity_id=user_id, request_id=self.request_id)
            raise NotFoundError("User", str(user_id))

        if data.username is not None and data.username != user.username:
            existing_user = await self.user_repo.get_by_username(data.username)
            if existing_user:
                self._log_error(f"User with username '{data.username}' already exists", request_id=self.request_id)
                raise AlreadyExistsError("User", f"username '{data.username}' already exists")

        data.update_model(user)

        try:
            await redis_client.delete(f"user:{user_id}")
            self._log_info("Cache invalidated for user", user_id=user_id, request_id=self.request_id)
        except Exception as e:
            self._log_warning(f"Redis error on delete: {e}", request_id=self.request_id)
        self._log_info("Updated user", entity_id=user.id, request_id=self.request_id)
        return UserResponse.model_validate(user)

    async def delete_user(self, user_id: UUID) -> None:
        self._log_info("Deleting user", entity_id=user_id, request_id=self.request_id)

        deleted = await self.user_repo.soft_delete(user_id)
        if not deleted:
            self._log_warning("User not found for delete", entity_id=user_id, request_id=self.request_id)
            raise NotFoundError("User", str(user_id))

        try:
            await redis_client.delete(f"user:{user_id}")
            self._log_info("Cache invalidated for deleted user", user_id=user_id, request_id=self.request_id)
        except Exception as e:
            self._log_warning(f"Redis error on delete: {e}", request_id=self.request_id)
        self._log_info("Deleted user", entity_id=user_id, request_id=self.request_id)

