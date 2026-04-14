from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.services.countries_cities import CountriesCitiesService
from src.schemas.countries import CountryCreate, CountryUpdate, CountryResponse
from src.db import get_session

router = APIRouter(prefix="/v1/countries-cities", tags=["Countries & Cities"])

@router.post("/", response_model=CountryResponse, status_code=status.HTTP_201_CREATED)
async def create_country(
    data: CountryCreate,
    db: AsyncSession = Depends(get_session)):
    service = CountriesCitiesService(db=db)
    result = await service.create_country(data=data)
    return result

@router.get("/{country_id}", response_model=CountryResponse)
async def get_country(
    country_id: UUID,
    db: AsyncSession = Depends(get_session)):
    service = CountriesCitiesService(db=db)
    result = await service.get_country(country_id=country_id)
    return result

@router.put("/{country_id}", response_model=CountryResponse)
async def update_country(
    country_id: UUID,
    data: CountryUpdate,
    db: AsyncSession = Depends(get_session)):
    service = CountriesCitiesService(db=db)
    result = await service.update_country(country_id=country_id, data=data)
    return result

@router.delete("/{country_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_country(
    country_id: UUID,
    db: AsyncSession = Depends(get_session)):
    service = CountriesCitiesService(db=db)
    await service.delete_country(country_id=country_id)
