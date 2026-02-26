from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.services.passports import PassportService
from src.schemas.passports import PassportCreate, PassportUpdate, PassportResponse
from src.db import get_session

router = APIRouter(prefix="/passports", tags=["Passports"])

@router.post("/", response_model=PassportResponse, status_code=status.HTTP_201_CREATED)
async def create_passport(
    data: PassportCreate,
    db: AsyncSession = Depends(get_session)):
    """
    Создание нового паспорта и привязка к пользователю.
    :param data: данные паспорта (passport_number, user_id)
    :return: PassportResponse: созданный паспорт (без user_id)
    """
    return await PassportService.create(db, data)

@router.get("/{passport_id}", response_model=PassportResponse)
async def get_passport(
    passport_id: UUID,
    db: AsyncSession = Depends(get_session)):
    """
    Получение паспорта по ID.
    :param passport_id: UUID паспорта
    :return: PassportResponse: паспорт (без user_id)
    """
    return await PassportService.get_by_id(db, passport_id)

@router.get("/by-user/{user_id}", response_model=PassportResponse)
async def get_passport_by_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_session)):
    """
    Получение паспорта по ID пользователя.
    :param user_id: UUID пользователя
    :return: PassportResponse: паспорт пользователя (без user_id)
    """
    return await PassportService.get_by_user_id(db, user_id)

@router.put("/{passport_id}", response_model=PassportResponse)
async def update_passport(
    passport_id: UUID,
    data: PassportUpdate,
    db: AsyncSession = Depends(get_session)):
    """
    Обновление паспорта (user_id не меняется).
    :param passport_id: UUID паспорта
    :param data: новые данные (passport_number)
    :return: PassportResponse: обновлённый паспорт
    """
    return await PassportService.update(db, passport_id, data)

@router.delete("/{passport_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_passport(
    passport_id: UUID,
    db: AsyncSession = Depends(get_session)):
   """
   Удаление паспорта по ID.
   :param passport_id: UUID паспорта
   :return: 204 No Content при успешном удалении
   """
   await PassportService.delete(db, passport_id)
   return None