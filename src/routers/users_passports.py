from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.services.users_passports import UsersPassportsService
from src.schemas.users import UserCreate, UserUpdate, UserResponse
from src.schemas.passports import PassportCreate, PassportUpdate, PassportResponse
from src.db import get_session
from src.schemas.base import StatusResponse

router = APIRouter(prefix="/v1/users-passports", tags=["Users & Passports"])

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_session)):

    return await UsersPassportsService.create_users(db, data)

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_session)):

    return await UsersPassportsService.get_user(db, user_id)

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_session)):

    return await UsersPassportsService.update_user(db, user_id, data)

@router.delete("/users/{user_id}", response_model=StatusResponse, status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_session)):

    await UsersPassportsService.delete_user(db, user_id)
    return StatusResponse(status="deleted")

@router.post("/passports", response_model=PassportResponse, status_code=status.HTTP_201_CREATED)
async def create_passport(
    data: PassportCreate,
    db: AsyncSession = Depends(get_session)):

    return await UsersPassportsService.create_passport(db, data)

@router.get("/passports/{passport_id}", response_model=PassportResponse)
async def get_passport(
    passport_id: UUID,
    db: AsyncSession = Depends(get_session)):

    return await UsersPassportsService.get_passport(db, passport_id)

@router.get("/passports/by-user/{user_id}", response_model=PassportResponse)
async def get_passport_by_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_session)):

    return await UsersPassportsService.get_passport_by_user(db, user_id)

@router.put("/passports/{passport_id}", response_model=PassportResponse)
async def update_passport(
    passport_id: UUID,
    data: PassportUpdate,
    db: AsyncSession = Depends(get_session)):

    return await UsersPassportsService.update_passport(db, passport_id, data)

@router.delete("/passports/{passport_id}", response_model=StatusResponse, status_code=status.HTTP_204_NO_CONTENT)
async def delete_passport(
    passport_id: UUID,
    db: AsyncSession = Depends(get_session)):

   await UsersPassportsService.delete_passport(db, passport_id)
   return StatusResponse(status="deleted")
