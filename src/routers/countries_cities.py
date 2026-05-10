from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from src.services.countries_cities import CountriesCitiesService
from src.schemas.countries import CountryCreate, CountryUpdate, CountryResponse
from src.db import get_session

router = APIRouter(prefix="/v1/countries-cities", tags=["Countries & Cities"])

@router.post("/", response_model=CountryResponse, status_code=status.HTTP_201_CREATED)
async def create_country(
    data: CountryCreate,
    db: AsyncSession = Depends(get_session)):

    return CountriesCitiesService(db=db).create_country(data=data)

@router.get("/{country_id}", response_model=CountryResponse)
async def get_country(
    country_id: UUID,
    db: AsyncSession = Depends(get_session)):

    return CountriesCitiesService(db=db).get_country(country_id=country_id)

@router.get("/countries", response_model=List[CountryResponse])
async def get_countries(
    skip: int = Query(0, ge=0, decription="Количество пропускаемых строк"),
    limit: int = Query(100, ge=1, le=100, description="Количество записей на странице"),
    db: AsyncSession = Depends(get_session)):
    return await CountriesCitiesService(db=db).get_countries(skip=skip, limit=limit)


@router.put("/{country_id}", response_model=CountryResponse)
async def update_country(
    country_id: UUID,
    data: CountryUpdate,
    db: AsyncSession = Depends(get_session)):

    return CountriesCitiesService(db=db).update_country(country_id=country_id, data=data)

@router.delete("/{country_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_country(
    country_id: UUID,
    db: AsyncSession = Depends(get_session)):

    await CountriesCitiesService(db=db).delete_country(country_id=country_id)
