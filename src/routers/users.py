from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.services.users import UserService
from src.schemas.users import UserCreate, UserUpdate, UserResponse
from src.db import get_session

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_session)):
    """
    Создание нового пользователя.
    :param data: данные пользователя (username, phone)
    :return: UserResponse: созданный пользователь
    """
    return await UserService.create(db, data)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_session)):
    """
    Получение пользователя по ID.
    :param user_id: UUID пользователя
    :return: UserResponse: пользователь
    """
    return await UserService.get_by_id(db, user_id)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_session)):
    """
    Обновление пользователя.
    :param user_id: UUID пользователя
    :param data: новые данные (username, phone)
    :return: UserResponse: обновлённый пользователь
    """
    return await UserService.update(db, user_id, data)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_session)):
    """
    Удаление пользователя по ID.
    :param user_id: UUID пользователя
    :return: 204 No Content при успешном удалении
    """
    await UserService.delete(db, user_id)
    return None
