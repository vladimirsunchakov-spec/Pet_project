from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.exceptions import NotFoundError
from src.services.base import BaseService
from utils.request_id import get_request_id
from src.schemas.users import UserCreate, UserUpdate, UserResponse
from src.redis import redis_client
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

        user_data = data.model_dump()
        user = await self.user_repo.upsert_user(user_data)

        self._log_info("Created user", entity_id=user.id, request_id=self.request_id)
        return UserResponse.model_validate(user)

    async def get_user(self, user_id: UUID) -> UserResponse:
        self._log_info("Fetching user", entity_id=user_id, request_id=self.request_id)

        cache_key = f"user:{user_id}"
        cached = await redis_client.get_cached(cache_key, UserResponse)
        if cached:
            self._log_info("Cache HIT for user", entity_id=user_id, request_id=self.request_id)
            return cached
        self._log_info("Cache MISS for user", entity_id=user_id, request_id=self.request_id)

        user = await self.user_repo.get_with_passport(user_id)
        if not user:
            self._log_warning("User not found", user_id=user_id, request_id=self.request_id)
            raise NotFoundError("User", str(user_id))
        response = UserResponse.model_validate(user)

        await redis_client.set_cached(cache_key, response)

        return response

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        self._log_info("Fetching users list", skip=skip, limit=limit, request_id=self.request_id)

        users = await self.user_repo.get_all_with_relations(skip=skip, limit=limit, relations=["passport"])

        self._log_info("Users fetched", count=len(users), request_id=self.request_id)
        return UserResponse.from_model_list(users)

    async def update_user(self, user_id: UUID, data: UserUpdate) -> UserResponse:
        self._log_info("Updating user", entity_id=user_id, request_id=self.request_id)

        user = await self.user_repo.get_with_passport_for_update(user_id)
        if not user:
            self._log_warning("User not found for update", entity_id=user_id, request_id=self.request_id)
            raise NotFoundError("User", str(user_id))

        data.update_model(user)

        user_data = data.model_dump(exclude_unset=True)
        if user_data:
            user_data["id"] = user_id
            await self.user_repo.upsert_user(user_data)

        await redis_client.invalidate(f"user:{user_id}")

        self._log_info("Updated user", entity_id=user.id, request_id=self.request_id)
        return UserResponse.model_validate(user)

    async def delete_user(self, user_id: UUID) -> None:
        self._log_info("Deleting user", entity_id=user_id, request_id=self.request_id)

        deleted = await self.user_repo.soft_delete(user_id)
        if not deleted:
            self._log_warning("User not found for delete", entity_id=user_id, request_id=self.request_id)
            raise NotFoundError("User", str(user_id))

        await redis_client.invalidate(f"user:{user_id}")

        self._log_info("Deleted user", entity_id=user_id, request_id=self.request_id)

