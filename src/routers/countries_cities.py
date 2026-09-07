from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from src.services.countries_cities import CountriesCitiesService
from src.schemas.countries import CountryCreate, CountryUpdate, CountryResponse
from src.schemas.cities import CityResponse, CityCreate
from src.db import get_session
from src.exceptions import NotFoundError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/countries", tags=["Countries & Cities"])

async def get_countries_service(
    db: AsyncSession = Depends(get_session)
) -> CountriesCitiesService:
    return CountriesCitiesService(db)

@router.post("/", response_model=CountryResponse, status_code=status.HTTP_201_CREATED, summary="Создать страну")
async def create_country(
    data: CountryCreate,
    service: CountriesCitiesService = Depends(get_countries_service),
):
    try:
        return await service.create_country(data)
    except Exception as e:
        logger.error(f"Failed to create country: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to create country: {str(e)}")

@router.get("/{country_id}", response_model=CountryResponse, summary="Получить страну по id")
async def get_country(
    country_id: UUID,
    service: CountriesCitiesService = Depends(get_countries_service)
):
    try:
        return await service.get_country(country_id)
    except NotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Failed to get country: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get country: {str(e)}")

@router.get("/countries", response_model=List[CountryResponse], summary="Получить все страны")
async def get_countries(
    skip: int = Query(0, ge=0, description="Количество пропускаемых строк"),
    limit: int = Query(100, ge=1, le=100, description="Количество записей на странице"),
    service: CountriesCitiesService = Depends(get_countries_service),
):
    try:
        return await service.get_countries(skip, limit)
    except Exception as e:
        logger.error(f"Failed to get countries: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get countries: {str(e)}")

@router.put("/{country_id}", response_model=CountryResponse, summary="Обновить страну")
async def update_country(
    country_id: UUID,
    data: CountryUpdate,
    service: CountriesCitiesService = Depends(get_countries_service),
):
    try:
        return await service.update_country(country_id, data)
    except NotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Failed to update country: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to update country: {str(e)}")

@router.delete("/{country_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить страну")
async def delete_country(
    country_id: UUID,
    service: CountriesCitiesService = Depends(get_countries_service),
):
    try:
        return await service.delete_country(country_id)
    except NotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Failed to delete country: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to delete country: {str(e)}")

@router.post("/{country_id}/cities", response_model=List[CityResponse], status_code=status.HTTP_201_CREATED, summary="Добавить города к стране")
async def add_city_to_country(
    country_id: UUID,
    cities: List[CityCreate],
    service: CountriesCitiesService = Depends(get_countries_service),
):
    try:
        return await service.add_city_to_country(country_id, cities)
    except NotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Failed to add city to country: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to add city to country: {str(e)}")