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
    def __init__(self, db: AsyncSession):
        self.db = db
        self.request_id = get_request_id()

    async def create_user(self, data: UserCreate, **kwargs) -> UserResponse:
        self._log_info("Creating user", request_id=self.request_id, username=data.username, phone=data.phone)

        await self._check_username_uniqueness(data.username)
        await self._check_phone_uniqueness(data.phone)

        user = UserModel.from_schema(data)
        self.db.add(user)

        if data.passport:
            passport = PassportModel.from_schema(data.passport)
            self.db.add(passport)
            user.passport = passport

        await self.db.refresh(user)

        self._log_info("Created user", entity_id=user.id,  request_id=self.request_id)
        return UserResponse.model_validate(user)

    async def get_user(self, user_id: UUID, **kwargs) -> UserResponse:
        self._log_info("Fetching user", entity_id=user_id, request_id=self.request_id)

        query = select(UserModel).where(UserModel.id == user_id)
        result = await self.db.execute(query)
        user =  result.scalar_one_or_none()

        if not user:
            self._log_warning("User not found", entity_id=user_id, request_id=self.request_id)
            raise NotFoundError("User", str(user_id))

        return UserResponse.model_validate(user)

    async def update_user(self, user_id: UUID, data:UserUpdate, **kwargs) -> UserResponse:
        self._log_info("Updating user", entity_id=user_id, request_id=self.request_id)

        user = await self.get_user(user_id=user_id)

        if data.username and data.username != user.username:
            await self._check_username_uniqueness(data.username, exclude_id=user.id)

        if data.phone and data.phone != user.phone:
            await self._check_phone_uniqueness(data.phone, exclude_id=user.id)

        user.update_from_schema(data)

        if data.passport:
            if user.passport:
                if data.passport.passport_number != user.passport.passport_number:
                    user.passport.passport_number = data.passport.passport_number
            else:
                passport = PassportModel.from_schema(data.passport)
                self.db.add(passport)
                user.passport = passport

        await self.db.refresh(user)

        self._log_info("Updated user", entity_id=user.id, request_id=self.request_id)
        return UserResponse.model_validate(user)

    async def delete_user(self, user_id: UUID, **kwargs) -> None:
        self._log_info("Deleting user", entity_id=user_id, request_id=self.request_id)

        user = await self.get_user(user_id=user_id)
        await self.db.delete(user)

        self._log_info("Deleted user", entity_id=user.id, request_id=self.request_id)

    async def _check_username_uniqueness(self, username: str, exclude_id: UUID | None = None) -> None:
        query = select(UserModel).where(UserModel.username == username)
        if exclude_id:
            query = query.where(UserModel.id != exclude_id)
        result = await self.db.execute(query)
        if result.scalar_one_or_none():
            raise UsernameAlreadyExistsError(username)

    async def _check_phone_uniqueness(self, phone: str, exclude_id: UUID | None = None) -> None:
        query = select(UserModel).where(UserModel.phone == phone)
        if exclude_id:
            query = query.where(UserModel.id != exclude_id)
        result = await self.db.execute(query)
        if result.scalar_one_or_none():
            raise PhoneAlreadyExistsError(phone)