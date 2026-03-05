from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.services.cities import CityService
from src.schemas.cities import CityCreate, CityUpdate, CityResponse
from src.db import get_session
from src.schemas.base import StatusResponse

router = APIRouter(prefix="/v1/cities", tags=["Cities"])

@router.post("/", response_model=CityResponse, status_code=status.HTTP_201_CREATED)
async def create_city(
    data: CityCreate,
    country_id: UUID,
    db: AsyncSession = Depends(get_session)):

    return await CityService.create(db, data, country_id)

@router.get("/{city_id}", response_model=CityResponse)
async def get_city(
    city_id: UUID,
    db: AsyncSession = Depends(get_session)):

    return await CityService.get_by_id(db, city_id)

@router.put("/{city_id}", response_model=CityResponse)
async def update_city(
    city_id: UUID,
    data: CityUpdate,
    db: AsyncSession = Depends(get_session)):

    return await CityService.update(db, city_id, data)

@router.delete("/{city_id}", response_model=StatusResponse, status_code=status.HTTP_204_NO_CONTENT)
async def delete_city(
    city_id: UUID,
    db: AsyncSession = Depends(get_session)):

    await CityService.delete(db, city_id)
    return StatusResponse(status="deleted")