from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.services.countries import CountryService
from src.schemas.countries import CountryCreate, CountryUpdate, CountryResponse
from src.db import get_session

router = APIRouter(prefix="/countries", tags=["Countries"])

@router.post("/", response_model=CountryResponse, status_code=status.HTTP_201_CREATED)
async def create_country(
    data: CountryCreate,
    db: AsyncSession = Depends(get_session)):
    """
    Создание новой страны с вложенными городами.
    :param data: данные страны (name, continent, cities)
    :return: CountryResponse: созданная страна со списком городов
    """
    return await CountryService.create(db, data)

@router.get("/{country_id}", response_model=CountryResponse)
async def get_country(
    country_id: UUID,
    db: AsyncSession = Depends(get_session)):
    """
    Получение страны по ID.
    :param country_id: UUID страны
    :return: CountryResponse: страна со списком городов
    """
    return await CountryService.get_by_id(db, country_id)

@router.put("/{country_id}", response_model=CountryResponse)
async def update_country(
    country_id: UUID,
    data: CountryUpdate,
    db: AsyncSession = Depends(get_session)):
    """
    Полное обновление страны и её городов.
    :param country_id: UUID страны
    :param data: новые данные (name, continent, cities)
    :return: CountryResponse: обновлённая страна
    """
    return await CountryService.update(db, country_id, data)

@router.delete("/{country_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_country(
    country_id: UUID,
    db: AsyncSession = Depends(get_session)):
    """
    Удаление страны по ID.
    :param country_id: UUID страны
    :return: 204 No Content при успешном удалении
    """
    await CountryService.delete(db, country_id)
    return None