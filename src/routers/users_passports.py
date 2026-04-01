from fastapi import APIRouter, Depends, status, Request
from src.exceptions import NotFoundError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.services.users_passports import UsersPassportsService
from src.schemas.users import UserCreate, UserUpdate, UserResponse
from src.schemas.passports import PassportCreate, PassportUpdate, PassportResponse
from src.db import get_session
from src.schemas.base import StatusResponse

router = APIRouter(prefix="/v1/users-passports", tags=["Users & Passports"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_session)):
    params = {
        "db": db,
        "data": data
    }
    user = await UsersPassportsService.create_user(**params)
    return UserResponse.model_validate(user)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_session)):
    params = {
        "db": db,
        "user_id": user_id
    }
    user = await UsersPassportsService.get_user(**params)
    if not user:
        raise NotFoundError("User not found")

    return UserResponse.model_validate(user)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_session)):
    params = {
        "db": db,
        "user_id": user_id,
        "data": data
    }
    user = await UsersPassportsService.update_user(**params)
    return UserResponse.model_validate(user)

@router.delete("/{user_id}", response_model=StatusResponse, status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_session)):
    params = {
        "db": db,
        "user_id": user_id
    }
    await UsersPassportsService.delete_user(**params)


@router.post("/passports", response_model=PassportResponse, status_code=status.HTTP_201_CREATED)
async def create_passport(
    data: PassportCreate,
    db: AsyncSession = Depends(get_session)):
    params = {
        "db": db,
        "data": data
    }
    passport = await UsersPassportsService.create_passport(**params)
    return PassportResponse.model_validate(passport)

@router.get("/passports/{passport_id}", response_model=PassportResponse)
async def get_passport(
    passport_id: UUID,
    db: AsyncSession = Depends(get_session)):
    params = {
        "db": db,
        "passport_id": passport_id
    }
    passport = await UsersPassportsService.get_passport(**params)
    if not passport:
        raise NotFoundError("Passport not found")
    return PassportResponse.model_validate(passport)

@router.put("/passports/{passport_id}", response_model=PassportResponse)
async def update_passport(
    passport_id: UUID,
    data: PassportUpdate,
    db: AsyncSession = Depends(get_session)):
    params = {
        "db": db,
        "passport_id": passport_id,
        "data": data
    }
    passport = await UsersPassportsService.update_passport(**params)
    return PassportResponse.model_validate(passport)

@router.delete("/passports/{passport_id}", response_model=StatusResponse, status_code=status.HTTP_204_NO_CONTENT)
async def delete_passport(
    passport_id: UUID,
    db: AsyncSession = Depends(get_session)):
    params = {
        "db": db,
        "passport_id": passport_id
    }
    await UsersPassportsService.delete_passport(**params)


