from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from fastapi import HTTPException, status

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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists")
        # Проверяем, что phone уникален
        query = select(UserModel).where(UserModel.phone == data.phone)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone already exists")

        user = UserModel(username=data.username, phone=data.phone)
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found")

        return UserResponse.model_validate(user)

    @staticmethod
    async def update(db: AsyncSession, user_id: UUID, data: UserUpdate) -> UserResponse:
        # Обновление пользователя
        # Проверяем существование
        await UserService.get_by_id(db, user_id)
        # Проверяем уникальность username
        query = select(UserModel).where(
            UserModel.username == data.username,
            UserModel.id != user_id
        )
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists")
        # Проверяем уникальность phone
        query = select(UserModel).where(
            UserModel.phone == data.phone,
            UserModel.id != user_id)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone already exists")

        stmt = update(UserModel).where(UserModel.id == user_id).values(
            username=data.username,
            phone=data.phone
        )
        await db.execute(stmt)
        await db.commit()

        return await UserService.get_by_id(db, user_id)

    @staticmethod
    async def delete(db: AsyncSession, user_id: UUID) -> None:
        # Удаление пользователя, каскадно удалится паспорт
        user = await UserService.get_by_id(db, user_id)
        await db.delete(user)
        await db.commit()