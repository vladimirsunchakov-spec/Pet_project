from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from src.exceptions import NotFoundError, ConflictError

from src.models.users import UserModel
from src.schemas.users import UserCreate, UserUpdate, UserResponse

class UserService:
    @staticmethod
    async def create(db: AsyncSession, data: UserCreate) -> UserResponse:
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
    async def get_by_id(db: AsyncSession, user_id: UUID) -> UserResponse:
        # Получение пользователя по ID
        query = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        return UserResponse.model_validate(user)

    @staticmethod
    async def update(db: AsyncSession, user_id: UUID, data: UserUpdate) -> UserResponse:
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
            raise ConflictError("Phone already exists")

        user.username = data.username
        user.phone = data.phone

        if result.scalar_one_or_none():
            raise ConflictError("Phone already exists")

        await db.commit()
        await db.refresh(user)

        return UserResponse.model_validate(user)

    @staticmethod
    async def delete(db: AsyncSession, user_id: UUID) -> None:
        # Удаление пользователя, каскадно удалится паспорт
        user = await UserService.get_by_id(db, user_id)
        await db.delete(user)
        await db.commit()

