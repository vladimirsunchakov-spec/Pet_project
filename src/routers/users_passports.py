from fastapi import APIRouter, Depends, status, Query, HTTPException
from src.dependencies import get_users_passports_service
from uuid import UUID
from src.exceptions import NotFoundError
from src.services.users_passports import UsersPassportsService
from src.schemas.users import UserCreate, UserUpdate, UserResponse
from src.schemas.passports import PassportCreate, PassportResponse
from typing  import List

router = APIRouter(prefix="/v1/users-passports", tags=["Users & Passports"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Создать пользователя")
async def create_user(
    data: UserCreate,
    service: UsersPassportsService = Depends(get_users_passports_service),):

    return await service.create_user(data)

@router.get("/{user_id}", response_model=UserResponse, summary="Получить пользователя")
async def get_user(
    user_id: UUID,
    service: UsersPassortsService = Depends(get_users_passports_service),):
    try:
        return await service.get_user(user_id)
    except NotFoundError as e:
        raise HTTPException (status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/users", response_model=List[UserResponse], summary="Получить пользователей")
async def get_users(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Количество записей на странице"),
    service: UsersPassportsService = Depends(get_users_passports_service),):

    return await service.get_users(skip=skip, limit=limit)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    service: UsersPassortsService = Depends(get_users_passports_service)):
    try:
        return await service.update_user(user_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить пользователя")
async def delete_user(
    user_id: UUID,
    service: UsersPassportsService = Depends(get_users_passports_service)):
    try:
        return await service.delete_user(user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
