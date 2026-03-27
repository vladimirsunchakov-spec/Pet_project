from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from src.exceptions import NotFoundError, ConflictError
from src.core.enums import StatusEnum
from src.services.base import BaseService
from src.middleware.request_id import get_request_id
from src.models.users import UserModel
from src.schemas.users import UserCreate, UserUpdate
from src.models.passports import PassportModel
from src.schemas.passports import PassportCreate, PassportUpdate
from src.schemas.base import StatusResponse

class UsersPassportsService(BaseService):
    @classmethod
    async def create_user(cls, db: AsyncSession, data: UserCreate, request_id: str | None = None) -> UserModel:
        if request_id is None:
            request_id = get_request_id()

        cls._log_info("Creating user", request_id=request_id, username=data.username, phone=data.phone)

        query = select(UserModel).where(UserModel.username == data.username)
        result = await db.execute(query)

        if result.scalar_one_or_none():
            cls._log_error("User already exists", request_id=request_id, username=data.username)
            raise ConflictError("Username", data.username)

        query = select(UserModel).where(UserModel.phone == data.phone)
        result = await db.execute(query)

        if result.scalar_one_or_none():
            cls._log_error("Phone already exists", request_id=request_id, phone=data.phone)
            raise ConflictError("Phone", data.phone)

        user = UserModel.from_schema(data)
        db.add(user)

        cls._log_info("Created user", entity_id=user.id,  request_id=request_id)

        return user

    @classmethod
    async def get_user(cls, db: AsyncSession, user_id: UUID, request_id: str | None =None) -> UserModel | None:
        if request_id is None:
            request_id = get_request_id()

        cls._log_info("Fetching user", entity_id=user_id, request_id=request_id)

        query = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(query)
        user =  result.scalar_one_or_none()

        if not user:
            cls._log_warning("User not found", entity_id=user_id, request_id=request_id)

        return user

    @classmethod
    async def update_user(cls, db: AsyncSession, user_id: UUID, data: UserUpdate, request_id: str | None = None) -> UserModel:
        if request_id is None:
            request_id = get_request_id()

        cls._log_info("Updating user", entity_id=user_id, request_id=request_id)

        user = await cls.get_user(db, user_id, request_id=request_id)

        if not user:
            cls._log_error("User not found for update", entity_id=user_id, request_id=request_id)
            raise NotFoundError("User", str(user_id))

        query = select(UserModel).where(
            UserModel.username == data.username,
            UserModel.id != user_id)
        result = await db.execute(query)

        if result.scalar_one_or_none():
            cls._log_error("User already exists for update", request_id=request_id, username=data.username)
            raise ConflictError("Username", data.username)

        query = select(UserModel).where(
            UserModel.phone == data.phone,
            UserModel.id != user_id)

        result = await db.execute(query)
        if result.scalar_one_or_none():
            cls._log_error("Phone already exists for update", request_id=request_id, phone=data.phone)
            raise ConflictError("Phone", data.phone)

        user.username = data.username
        user.phone = data.phone

        cls._log_info("Updated user", entity_id=user.id, request_id=request_id)

        return user

    @classmethod
    async def delete_user(cls, db: AsyncSession, user_id: UUID, request_id: str | None = None) -> StatusResponse:
        if request_id is None:
            request_id = get_request_id()
        cls._log_info("Deleting user", entity_id=user_id, request_id=request_id)

        user = await cls.get_user(db, user_id, request_id=request_id)
        if not user:
            cls._log_error("User not found for deletion", entity_id=user_id, request_id=request_id)
            raise NotFoundError("User", str(user_id))

        await db.delete(user)
        cls._log_info("Deleted user", entity_id=user.id, request_id=request_id)
        return StatusResponse(status=StatusEnum.DELETED)

    @classmethod
    async def create_passport(cls, db: AsyncSession, data: PassportCreate, request_id: str | None = None) -> PassportModel:
        if request_id is None:
            request_id = get_request_id()

        cls._log_info("Creating passport", request_id=request_id, passport_number=data.passport_number, user_id=str(data.user_id))

        user = await cls.get_user(db, data.user_id, request_id=request_id)

        if not user:
            cls._log_error("User not found for passport creation", entity_id=data.user_id, request_id=request_id)
            raise NotFoundError("User", str(data.user_id))

        query = select(PassportModel).where(PassportModel.user_id == data.user_id)
        result = await db.execute(query)

        if result.scalar_one_or_none():
            cls._log_error("User already has a passport", entity_id=data.user_id, request_id=request_id)
            raise ConflictError("User", str(data.user_id))

        query = select(PassportModel).where(PassportModel.passport_number == data.passport_number)
        result = await db.execute(query)

        if result.scalar_one_or_none():
            cls._log_error("Passport number already exists", request_id=request_id, passport_number=data.passport_number)
            raise ConflictError("Passport number", data.passport_number)

        passport = PassportModel.from_schema(data)
        db.add(passport)

        cls._log_info("Created passport", entity_id=passport.id, request_id=request_id, user_id=str(data.user_id))

        return passport

    @classmethod
    async def get_passport(cls, db: AsyncSession, passport_id: UUID, request_id: str | None = None) -> PassportModel | None:
        if request_id is None:
            request_id = get_request_id()

        cls._log_info("Fetching passport", entity_id=passport_id, request_id=request_id)

        query = select(PassportModel).where(PassportModel.id == passport_id)
        result = await db.execute(query)
        passport = result.scalar_one_or_none()

        if not passport:
            cls._log_warning("Passport not found", entity_id=passport_id, request_id=request_id)

        return passport

    @classmethod
    async def get_passport_by_user(cls, db: AsyncSession, user_id: UUID, request_id: str | None = None) -> PassportModel | None:
        if request_id is None:
            request_id = get_request_id()

        cls._log_info("Fetching passport", entity_id=user_id, request_id=request_id)

        query = select(PassportModel).where(PassportModel.user_id == user_id)
        result = await db.execute(query)
        passport = result.scalar_one_or_none()

        if not passport:
            cls._log_warning("Passport not found for user", entity_id=user_id, request_id=request_id)

        return passport

    @classmethod
    async def update_passport(cls, db: AsyncSession, passport_id: UUID, data: PassportUpdate, request_id: str | None = None) -> PassportModel:
        if request_id is None:
            request_id = get_request_id()

        cls._log_info("Updating passport", entity_id=passport_id, request_id=request_id)

        passport = await cls.get_passport(db, passport_id, request_id=request_id)

        if not passport:
            cls._log_error("Passport not found for update", entity_id=passport_id, request_id=request_id)
            raise NotFoundError("Passport", str(passport_id))

        query = select(PassportModel).where(
            PassportModel.passport_number == data.passport_number,
            PassportModel.id != passport_id
        )
        result = await db.execute(query)
        if result.scalar_one_or_none():
            cls._log_error("Passport number already exists for update", request_id=request_id, passport_number=data.passport_number)
            raise ConflictError("Passport number", data.passport_number)

        passport.passport_number = data.passport_number

        cls._log_info("Passport updated", entity_id=passport.id, request_id=request_id)

        return passport

    @classmethod
    async def delete_passport(cls, db: AsyncSession, passport_id: UUID, request_id: str | None = None) -> StatusResponse:
        if request_id is None:
            request_id = get_request_id()

        cls._log_info("Deleting passport", entity_id=passport_id, request_id=request_id)

        passport = await cls.get_passport(db, passport_id, request_id=request_id)

        if not passport:
            cls._log_error("Passport not found for deletion", entity_id=passport_id, request_id=request_id)
            raise NotFoundError("Passport", str(passport_id))

        await db.delete(passport)

        cls._log_info("Deleted passport", entity_id=passport.id, request_id=request_id)

        return StatusResponse(status=StatusEnum.DELETED)

