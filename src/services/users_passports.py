from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from schemas.users import UserResponse
from src.exceptions import (
    NotFoundError,
    UserAlreadyHasPassportError,
    PhoneAlreadyExistsError,
    UsernameAlreadyExistsError,
    PassportAlreadyExistsError)

from src.services.base import BaseService
from src.middleware.request_id import get_request_id
from src.models.users import UserModel
from src.schemas.users import UserCreate, UserUpdate
from src.models.passports import PassportModel


class UsersPassportsService(BaseService):
    def __init__(self, **kwargs):
        self.db: AsyncSession = kwargs.get("db")
        self.request_id: str = kwargs.get("request_id", get_request_id())

    async def create_user(self, **kwargs) -> UserModel:
        data = kwargs.get("data")
        self._log_info("Creating user", request_id=self.request_id, username=data.username, phone=data.phone)

        await self._check_uniqueness(
            db=self.db,
            model=UserModel,
            fields={"username": data.username, "phone": data.phone},
            request_id=self.request_id,
        )

        user = UserModel.from_schema(data)
        self.db.add(user)
        if data.passport:
            passport = PassportModel.from_schema(data.passport)
            self.db.add(passport)
            user.passport = passport

        await self.db.refresh(user)

        self._log_info("Created user", entity_id=user.id,  request_id=self.request_id)
        return UserResponse.model_validate(user)

    async def get_user(self, **kwargs) -> UserModel:
        user_id = kwargs.get("user_id")
        self._log_info("Fetching user", entity_id=user_id, request_id=self.request_id)

        query = select(UserModel).where(UserModel.id == user_id)
        result = await self.db.execute(query)
        user =  result.scalar_one_or_none()

        if not user:
            self._log_warning("User not found", entity_id=user_id, request_id=self.request_id)
            raise NotFoundError("User", str(user_id))

        return UserResponse.model_validate(user)

    async def update_user(self, **kwargs) -> UserModel:
        user_id = kwargs.get("user_id")
        data = kwargs.get("data")
        self._log_info("Updating user", entity_id=user_id, request_id=self.request_id)

        user = await self.get_user(user_id=user_id)

        await self._check_uniqueness(
            db=self.db,
            model=UserModel,
            fields={"username": data.username, "phone": data.phone},
            exclude_id=user_id,
            request_id=self.request_id)

        user.username = data.username
        user.phone = data.phone

        if data.passport:
            if user.passport:
                user.passport.passport_number = data.passport.passport_number
            else:
                passport = PassportModel.from_schema(data.passport)
                self.db.add(passport)
                user.passport = passport

        await self.db.refresh(user)

        self._log_info("Updated user", entity_id=user.id, request_id=self.request_id)
        return UserResponse.model_validate(user)

    async def delete_user(self, **kwargs) -> None:
        user_id = kwargs.get("user_id")
        self._log_info("Deleting user", entity_id=user_id, request_id=self.request_id)

        user = await self.get_user(user_id=user_id)
        await self.db.delete(user)

        self._log_info("Deleted user", entity_id=user.id, request_id=self.request_id)
