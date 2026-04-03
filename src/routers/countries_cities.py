from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.services.countries_cities import CountriesCitiesService
from src.schemas.countries import CountryCreate, CountryUpdate, CountryResponse
from src.schemas.cities import CityCreate, CityUpdate, CityResponse
from src.schemas.base import StatusResponse
from src.db import get_session
from src.exceptions import NotFoundError

router = APIRouter(prefix="/v1/countries-cities", tags=["Countries & Cities"])

@router.post("/", response_model=CountryResponse, status_code=status.HTTP_201_CREATED)
async def create_country(
    data: CountryCreate,
    db: AsyncSession = Depends(get_session)):
    country = await CountriesCitiesService.create_country(data=data, db=db)
    return CountryResponse.model_validate(country)

@router.get("/{country_id}", response_model=CountryResponse)
async def get_country(
    country_id: UUID,
    db: AsyncSession = Depends(get_session)):
    country = await CountriesCitiesService.get_country(country_id=country_id, db=db)
    if not country:
        raise NotFoundError("Country not found")
    return CountryResponse.model_validate(country)

@router.put("/{country_id}", response_model=CountryResponse)
async def update_country(
    country_id: UUID,
    data: CountryUpdate,
    db: AsyncSession = Depends(get_session)):
    country = await CountriesCitiesService.update_country(country_id=country_id, data=data, db=db)
    return CountryResponse.model_validate(country)

@router.delete("/{country_id}", response_model=StatusResponse, status_code=status.HTTP_204_NO_CONTENT)
async def delete_country(
    country_id: UUID,
    db: AsyncSession = Depends(get_session)):
    await CountriesCitiesService.delete_country(country_id=country_id, db=db)

@router.post("/countries/{country_id}/cities", response_model=CityResponse, status_code=status.HTTP_201_CREATED)
async def create_city(
    country_id: UUID,
    data: CityCreate,
    db: AsyncSession = Depends(get_session)):
    city = await CountriesCitiesService.create_city(country_id=country_id, data=data, db=db)
    return CityResponse.model_validate(city)

@router.get("/cities/{city_id}", response_model=CityResponse)
async def get_city(
    city_id: UUID,
    db: AsyncSession = Depends(get_session)):
    city = await CountriesCitiesService.get_city(city_id=city_id, db=db)
    if not city:
        raise NotFoundError("City not found")
    return CityResponse.model_validate(city)

@router.put("/cities/{city_id}", response_model=CityResponse)
async def update_city(
    city_id: UUID,
    data: CityUpdate,
    db: AsyncSession = Depends(get_session)):
    city = await CountriesCitiesService.update_city(city_id=city_id, data=data, db=db)
    return CityResponse.model_validate(city)

@router.delete("/cities/{city_id}", response_model=StatusResponse, status_code=status.HTTP_204_NO_CONTENT)
async def delete_city(
    city_id: UUID,
    db: AsyncSession = Depends(get_session)):
    await CountriesCitiesService.delete_city(city_id=city_id, db=db)

