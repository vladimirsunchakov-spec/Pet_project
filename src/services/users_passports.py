from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from src.exceptions import NotFoundError, ConflictError

from src.models.users import UserModel
from src.schemas.users import UserCreate, UserUpdate
from src.models.passports import PassportModel
from src.schemas.passports import PassportCreate, PassportUpdate
from src.schemas.base import StatusResponse

class UsersPassportsService:
    @staticmethod
    async def create_users(db: AsyncSession, data: UserCreate) -> UserModel:
        query = select(UserModel).where(UserModel.username == data.username)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ConflictError("Username already exists")

        query = select(UserModel).where(UserModel.phone == data.phone)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ConflictError("Phone already exists")

        user = UserModel.from_schema(data)
        db.add(user)
        return user

    @staticmethod
    async def get_user(db: AsyncSession, user_id: UUID) -> UserModel | None:
        query = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_user(db: AsyncSession, user_id: UUID, data: UserUpdate) -> UserModel:
        user = await UsersPassportsService.get_user(db, user_id, data)

        if not user:
            raise NotFoundError("User not found")

        query = select(UserModel).where(
            UserModel.username == data.username,
            UserModel.id != user_id
        )
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ConflictError("Username already exists")

        query = select(UserModel).where(
            UserModel.phone == data.phone,
            UserModel.id != user_id)

        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ConflictError("Phone already exists")

        user.username = data.username
        user.phone = data.phone
        return user

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: UUID) -> StatusResponse:
        user = await UsersPassportsService.get_user(db, user_id)

        if not user:
            raise NotFoundError("User not found")

        await db.delete(user)
        return StatusResponse(status="deleted")

    @staticmethod
    async def create_passport(db: AsyncSession, data: PassportCreate) -> PassportModel:
        user = await UsersPassportsService.get_user(db, data.user_id)

        if not user:
            raise NotFoundError("User not found")

        query = select(PassportModel).where(PassportModel.user_id == data.user_id)
        result = await db.execute(query)

        if result.scalar_one_or_none():
            raise ConflictError("User already has a passport")

        query = select(PassportModel).where(PassportModel.passport_number == data.passport_number)
        result = await db.execute(query)

        if result.scalar_one_or_none():
            raise ConflictError("Passport number already exists")

        passport = PassportModel.from_schema(data)
        db.add(passport)
        return passport

    @staticmethod
    async def get_passport(db: AsyncSession, passport_id: UUID) -> PassportModel:
        query = select(PassportModel).where(PassportModel.id == passport_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_passport_by_user(db: AsyncSession, user_id: UUID) -> PassportModel | None:
        query = select(PassportModel).where(PassportModel.user_id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_passport(db: AsyncSession, passport_id: UUID, data: PassportUpdate) -> PassportModel:
        passport = await UsersPassportsService.get_passport(db, passport_id)

        if not passport:
            raise NotFoundError("Passport not found")

        query = select(PassportModel).where(
            PassportModel.passport_number == data.passport_number,
            PassportModel.id != passport_id
        )
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ConflictError("Passport number already exists")

        passport.passport_number = data.passport_number
        return passport

    @staticmethod
    async def delete_passport(db: AsyncSession, passport_id: UUID) -> StatusResponse:
        passport = await UsersPassportsService.get_passport(db, passport_id)

        if not passport:
            raise NotFoundError("Passport not found")

        await db.delete(passport)
        return StatusResponse(status="deleted")

