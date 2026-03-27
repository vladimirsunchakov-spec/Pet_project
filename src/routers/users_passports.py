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
    request: Request,
    data: UserCreate,
    db: AsyncSession = Depends(get_session)):
    user = await UsersPassportsService.create_user(db=db, data=data, request_id=request.state.request_id)
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    request: Request,
    user_id: UUID,
    db: AsyncSession = Depends(get_session)):
    user = await UsersPassportsService.get_user(db=db, user_id=user_id, request_id=request.state.request_id)
    if not user:
        raise NotFoundError("User not found")

    return UserResponse.model_validate(user)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    request: Request,
    user_id: UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_session)):
    user = await UsersPassportsService.update_user(user_id=user_id, data=data, db=db, request_id=request.state.request_id)
    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)

@router.delete("/{user_id}", response_model=StatusResponse, status_code=status.HTTP_200_OK)
async def delete_user(
    request: Request,
    user_id: UUID,
    db: AsyncSession = Depends(get_session)):
    result = await UsersPassportsService.delete_user(user_id=user_id, db=db, request_id=request.state.request_id)
    await db.commit()
    return result

@router.post("/passports", response_model=PassportResponse, status_code=status.HTTP_201_CREATED)
async def create_passport(
    request: Request,
    data: PassportCreate,
    db: AsyncSession = Depends(get_session)):
    passport = await UsersPassportsService.create_passport(data=data, db=db, request_id=request.state.request_id)
    await db.commit()
    await db.refresh(passport)
    return PassportResponse.model_validate(passport)

@router.get("/passports/{passport_id}", response_model=PassportResponse)
async def get_passport(
    request: Request,
    passport_id: UUID,
    db: AsyncSession = Depends(get_session)):
    passport = await UsersPassportsService.get_passport(passport_id=passport_id, db=db, request_id=request.state.request_id)
    if not passport:
        raise NotFoundError("Passport not found")
    return PassportResponse.model_validate(passport)

@router.put("/passports/{passport_id}", response_model=PassportResponse)
async def update_passport(
    request: Request,
    passport_id: UUID,
    data: PassportUpdate,
    db: AsyncSession = Depends(get_session)):
    passport = await UsersPassportsService.update_passport(passport_id=passport_id, data=data, db=db, request_id=request.state.request_id)
    await db.commit()
    await db.refresh(passport)
    return PassportResponse.model_validate(passport)

@router.delete("/passports/{passport_id}", response_model=StatusResponse, status_code=status.HTTP_200_OK)
async def delete_passport(
    request: Request,
    passport_id: UUID,
    db: AsyncSession = Depends(get_session)):
    result = await UsersPassportsService.delete_passport(passport_id=passport_id, db=db, request_id=request.state.request_id)
    return result

