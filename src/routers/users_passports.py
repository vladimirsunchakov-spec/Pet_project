from fastapi import APIRouter, Depends, status
from keyring.backends.macOS.api import NotFound
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
    user = await UsersPassportsService.create_users(db, data)
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_session)):
    user = await UsersPassportsService.get_user(db, user_id)
    if not user:
        raise NotFound("User not found")

    return UserResponse.model_validate(user)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_session)):
    user = await UsersPassportsService.update_user(user_id, data, db)
    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)

@router.delete("/{user_id}", response_model=StatusResponse, status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_session)):
    result = await UsersPassportsService.delete_user(user_id, db)
    await db.commit()
    return result

@router.post("/passports", response_model=PassportResponse, status_code=status.HTTP_201_CREATED)
async def create_passport(
    data: PassportCreate,
    db: AsyncSession = Depends(get_session)):
    passport = await UsersPassportsService.create_passport(data, db)
    await db.commit()
    await db.refresh(passport)
    return PassportResponse.model_validate(passport)

@router.get("/passports/{passport_id}", response_model=PassportResponse)
async def get_passport(
    passport_id: UUID,
    db: AsyncSession = Depends(get_session)):
    passport = await UsersPassportsService.get_passport(passport_id, db)
    if not passport:
        raise NotFound("Passport not found")
    return PassportResponse.model_validate(passport)

@router.get("/passports/by-user/{user_id}", response_model=PassportResponse)
async def get_passport_by_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_session)):
    passport = await UsersPassportsService.get_passport_by_user(user_id, db)
    if not passport:
        raise NotFound("Passport not found for this user")
    return PassportResponse.model_validate(passport)

@router.put("/passports/{passport_id}", response_model=PassportResponse)
async def update_passport(
    passport_id: UUID,
    data: PassportUpdate,
    db: AsyncSession = Depends(get_session)):
    passport = await UsersPassportsService.update_passport(passport_id, data, db)
    await db.commit()
    await db.refresh(passport)
    return PassportResponse.model_validate(passport)

@router.delete("/passports/{passport_id}", response_model=StatusResponse, status_code=status.HTTP_200_OK)
async def delete_passport(
    passport_id: UUID,
    db: AsyncSession = Depends(get_session)):
    result = await UsersPassportsService.delete_passport(passport_id, db)
    return result

