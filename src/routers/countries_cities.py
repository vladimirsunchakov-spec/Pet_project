from fastapi import APIRouter, Depends, status, Query, HTTPException
from uuid import UUID
from typing import List
from src.services.countries_cities import CountriesCitiesService
from src.schemas.countries import CountryCreate, CountryUpdate, CountryResponse
from src.schemas.cities import CityResponse, CityCreate
from src.dependencies import get_countries_cities_service
from src.exceptions import NotFoundError

router = APIRouter(prefix="/v1/countries", tags=["Countries & Cities"])

@router.post("/", response_model=CountryResponse, status_code=status.HTTP_201_CREATED, summary="Создать страну")
async def create_country(
    data: CountryCreate,
    service: CountriesCitiesService = Depends(get_countries_cities_service),
):
    return await service.create_country(data)

@router.get("/{country_id}", response_model=CountryResponse, summary="Получить страну по id")
async def get_country(
    country_id: UUID,
    service: CountriesCitiesService = Depends(get_countries_cities_service),
):
    try:
        return await service.get_country(country_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/countries", response_model=List[CountryResponse], summary="Получить все страны")
async def get_countries(
    skip: int = Query(0, ge=0, description="Количество пропускаемых строк"),
    limit: int = Query(100, ge=1, le=100, description="Количество записей на странице"),
    service: CountriesCitiesService = Depends(get_countries_cities_service),
):
    return await service.get_countries(skip=skip, limit=limit)


@router.put("/{country_id}", response_model=CountryResponse, summary="Обновить страну")
async def update_country(
    country_id: UUID,
    data: CountryUpdate,
    service: CountriesCitiesService = Depends(get_countries_cities_service),
):
    try:
        return await service.update_country(country_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e),)

@router.delete("/{country_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить страну")
async def delete_country(
    country_id: UUID,
    service: CountriesCitiesService = Depends(get_countries_cities_service),
):
    try:
        await service.delete_country(country_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/{country_id}/cities", response_model=List[CityResponse], status_code=status.HTTP_201_CREATED, summary="Добавить города к стране")
async def add_city_to_country(
    country_id: UUID,
    cities: List[CityCreate],
    service: CountriesCitiesService = Depends(get_countries_cities_service),
):
    try:
        return await service.add_city_to_country(country_id, cities)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
