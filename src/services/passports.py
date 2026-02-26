from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from fastapi import HTTPException, status

from src.models.passports import PassportModel
from src.models.users import UserModel
from src.schemas.passports import PassportCreate, PassportUpdate, PassportResponse

class PassportService:
    @staticmethod
    async def create(db: AsyncSession, data: PassportCreate) -> PassportResponse:
        # Создание паспорта и привязка к пользователю
        # Проверяем, что пользователь существует
        query = select(UserModel).where(UserModel.id == data.user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found")
        # Проверяем, нет ли уже другого паспорта у этого пользователя
        query = select(PassportModel).where(PassportModel.user_id == data.user_id)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has a passport")
        # Проверяем уникальность номера паспорта
        query = select(PassportModel).where(PassportModel.passport_number == data.passport_number)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passport number already exists")
        # Создаем паспорт
        passport = PassportModel(
            passport_number=data.passport_number,
            user_id=data.user_id)
        db.add(passport)
        await db.commit()
        await db.refresh(passport)

        return PassportResponse.model_validate(passport)

    @staticmethod
    async def get_by_id(db: AsyncSession, passport_id: UUID) -> PassportResponse:
        # Получение паспорта по ID
        query = select(PassportModel).where(PassportModel.id == passport_id)
        result = await db.execute(query)
        passport = result.scalar_one_or_none()

        if not passport:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Passport not found")

        return PassportResponse.model_validate(passport)

    @staticmethod
    async def update(db: AsyncSession, passport_id: UUID, data: PassportUpdate) -> PassportResponse:
        # Обновление паспорта
        # Проверяем существование
        await PassportService.get_by_id(db, passport_id)
        # Проверяем уникальность номера
        query = select(PassportModel).where(
            PassportModel.passport_number == data.passport_number,
            PassportModel.id != passport_id
        )
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passport number already exists"
            )

        stmt = update(PassportModel).where(PassportModel.id == passport_id).values(
            passport_number=data.passport_number)
            # user_id не обновляем!
        await db.execute(stmt)
        await db.commit()

        return await PassportService.get_by_id(db, passport_id)

    @staticmethod
    async def delete(db: AsyncSession, passport_id: UUID) -> None:
        # Удаление паспорта
        passport = await PassportService.get_by_id(db, passport_id)
        await db.delete(passport)
        await db.commit()

    @staticmethod
    async def get_by_user_id(db: AsyncSession, user_id: UUID) -> PassportResponse:
        # Получение паспорта по ID пользователя
        query = select(PassportModel).where(PassportModel.user_id == user_id)
        result = await db.execute(query)
        passport = result.scalar_one_or_none()

        if not passport:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Passport not found for this user")

        return PassportResponse.model_validate(passport)
