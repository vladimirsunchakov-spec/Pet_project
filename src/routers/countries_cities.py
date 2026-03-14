from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.services.countries_cities import CountriesCitiesService
from src.schemas.countries import CountryCreate, CountryUpdate, CountryResponse
from src.schemas.cities import CityCreate, CityUpdate, CityResponse
from src.db import get_session
from src.schemas.base import StatusResponse

router = APIRouter(prefix="/v1/countries-cities", tags=["Countries & Cities"])

@router.post("countries/", response_model=CountryResponse, status_code=status.HTTP_201_CREATED)
async def create_country(
    data: CountryCreate,
    db: AsyncSession = Depends(get_session)):

    return await CountriesCitiesService.create_country(db, data)

@router.get("countries/{country_id}", response_model=CountryResponse)
async def get_country(
    country_id: UUID,
    db: AsyncSession = Depends(get_session)):

    return await CountriesCitiesService.get_country(db, country_id)

@router.put("countries/{country_id}", response_model=CountryResponse)
async def update_country(
    country_id: UUID,
    data: CountryUpdate,
    db: AsyncSession = Depends(get_session)):

    return await CountriesCitiesService.update_country(db, country_id, data)

@router.delete("countries/{country_id}", response_model=StatusResponse, status_code=status.HTTP_204_NO_CONTENT)
async def delete_country(
    country_id: UUID,
    db: AsyncSession = Depends(get_session)):

    await CountriesCitiesService.delete_country(db, country_id)
    return StatusResponse(status="deleted")

@router.post("/cities", response_model=CityResponse, status_code=status.HTTP_201_CREATED)
async def create_city(
    data: CityCreate,
    country_id: UUID,
    db: AsyncSession = Depends(get_session)):

    return await CountriesCitiesService.create_city(db, data, country_id)

@router.get("cities/{city_id}", response_model=CityResponse)
async def get_city(
    city_id: UUID,
    db: AsyncSession = Depends(get_session)):

    return await CountriesCitiesService.get_city(db, city_id)

@router.put("cities/{city_id}", response_model=CityResponse)
async def update_city(
    city_id: UUID,
    data: CityUpdate,
    db: AsyncSession = Depends(get_session)):

    return await CountriesCitiesService.update_city(db, city_id, data)

@router.delete("cities/{city_id}", response_model=StatusResponse, status_code=status.HTTP_204_NO_CONTENT)
async def delete_city(
    city_id: UUID,
    db: AsyncSession = Depends(get_session)):

    await CountriesCitiesService.delete_city(db, city_id)
    return StatusResponse(status="deleted")