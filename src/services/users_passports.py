from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.exceptions import NotFoundError
from src.services.base import BaseService
from utils.request_id import get_request_id
from src.schemas.users import UserCreate, UserUpdate, UserResponse
from src.redis_client import redis_client
from src.repositories.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)


class UsersPassportsService(BaseService):
    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db
        self.request_id = get_request_id()
        self.user_repo = UserRepository(db)

    async def create_user(self, data: UserCreate) -> UserResponse:
        async with self.db.begin_nested():
            user = await self.user_repo.upsert_user(data.to_model())

        logger.info(
            "User created",
            extra={"entity_id": str(user.id), "request_id": self.request_id},
        )
        return UserResponse.model_validate(user)

    async def get_user(self, user_id: UUID) -> UserResponse:
        cache_key = f"user:{user_id}"
        cached = await redis_client.get_cached(cache_key, UserResponse)
        if cached:
            return cached

        user = await self.user_repo.get_with_relations(user_id, relations=["passport"])
        if not user:
            raise NotFoundError("User", str(user_id))

        response = UserResponse.model_validate(user)
        await redis_client.set_cached(cache_key, response)
        return response

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        users = await self.user_repo.get_all_with_relations(
            skip=skip,
            limit=limit,
            relations=["passport"],
        )
        return UserResponse.from_model_list(users)

    async def update_user(self, user_id: UUID, data: UserUpdate) -> UserResponse:
        async with self.db.begin_nested():
            user = await self.user_repo.get_for_update(user_id, relations=["passport"])
            if not user:
                raise NotFoundError("User", str(user_id))

            data.update_model(user)
            await self.db.flush()

        await redis_client.invalidate(f"user:{user_id}")
        return UserResponse.model_validate(user)

    async def delete_user(self, user_id: UUID) -> None:
        deleted = await self.user_repo.soft_delete(user_id)
        if not deleted:
            raise NotFoundError("User", str(user_id))

        await redis_client.invalidate(f"user:{user_id}")
        logger.info(
            "User deleted",
            extra={"entity_id": str(user_id), "request_id": self.request_id},
        )
