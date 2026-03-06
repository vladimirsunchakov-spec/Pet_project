from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from src.exceptions import NotFoundError, ConflictError

from src.models.users import UserModel
from src.schemas.users import UserCreate, UserUpdate, UserResponse
from src.models.passports import PassportModel
from src.schemas.passports import PassportCreate, PassportUpdate, PassportResponse

class UsersPassportsService:
    @staticmethod
    async def create_users(db: AsyncSession, data: UserCreate) -> UserResponse:
        # Создание пользователя
        # Проверяем, что username уникален
        query = select(UserModel).where(UserModel.username == data.username)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ConflictError("Username already exists")
        # Проверяем, что phone уникален
        query = select(UserModel).where(UserModel.phone == data.phone)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ConflictError("Phone already exists")

        user = UserModel.from_schema(data)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        return UserResponse.model_validate(user)

    @staticmethod
    async def get_user(db: AsyncSession, user_id: UUID) -> UserResponse:
        # Получение пользователя по ID
        query = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        return UserResponse.model_validate(user)

    @staticmethod
    async def update_user(db: AsyncSession, user_id: UUID, data: UserUpdate) -> UserResponse:
        query = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")
        # Проверяем уникальность username
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

        await db.commit()
        await db.refresh(user)

        return UserResponse.model_validate(user)

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: UUID) -> None:
        # Удаление пользователя, каскадно удалится паспорт
        query = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        await db.delete(user)
        await db.commit()

    @staticmethod
    async def create_passport(db: AsyncSession, data: PassportCreate) -> PassportResponse:
        # Создание паспорта и привязка к пользователю
        # Проверяем, что пользователь существует
        query = select(UserModel).where(UserModel.id == data.user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")
        # Проверяем, нет ли уже другого паспорта у этого пользователя
        query = select(PassportModel).where(PassportModel.user_id == data.user_id)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ConflictError("User already has a passport")
        # Проверяем уникальность номера паспорта
        query = select(PassportModel).where(PassportModel.passport_number == data.passport_number)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ConflictError("Passport number already exists")
        # Создаем паспорт
        passport = PassportModel.from_schema(data)
        db.add(passport)
        await db.commit()
        await db.refresh(passport)

        return PassportResponse.model_validate(passport)

    @staticmethod
    async def get_passport(db: AsyncSession, passport_id: UUID) -> PassportResponse:
        # Получение паспорта по ID
        query = select(PassportModel).where(PassportModel.id == passport_id)
        result = await db.execute(query)
        passport = result.scalar_one_or_none()

        if not passport:
            raise NotFoundError("Passport not found")

        return PassportResponse.model_validate(passport)

    @staticmethod
    async def update_passport(db: AsyncSession, passport_id: UUID, data: PassportUpdate) -> PassportResponse:
        query = select(PassportModel).where(PassportModel.id == passport_id)
        result = await db.execute(query)
        passport = result.scalar_one_or_none()

        if not passport:
            raise NotFoundError("Passport not found")

        # Проверяем уникальность номера
        query = select(PassportModel).where(
            PassportModel.passport_number == data.passport_number,
            PassportModel.id != passport_id
        )
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ConflictError("Passport number already exists")

        passport.passport_number = data.passport_number

        await db.commit()
        await db.refresh(passport)

        return PassportResponse.model_validate(passport)

    @staticmethod
    async def delete_passport(db: AsyncSession, passport_id: UUID) -> None:
        query = select(PassportModel).where(PassportModel.user_id == user_id)
        result = await db.execute(query)
        passport = result.scalar_one_or_none()

        if not passport:
            raise NotFoundError("Passport not found")

        await db.delete(passport)
        await db.commit()

    @staticmethod
    async def get_passport_by_user(db: AsyncSession, user_id: UUID) -> PassportResponse:
        # Получение паспорта по ID пользователя
        query = select(PassportModel).where(PassportModel.user_id == user_id)
        result = await db.execute(query)
        passport = result.scalar_one_or_none()

        if not passport:
            raise NotFoundError("Passport not found for this user")

        return PassportResponse.model_validate(passport)