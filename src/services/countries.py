from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from fastapi import HTTPException, status

from src.models.countries import CountryModel
from src.models.cities import CityModel
from src.schemas.countries import CountryCreate, CountryUpdate, CountryResponse

class CountryService:
    @staticmethod
    async def create(db: AsyncSession, data: CountryCreate) -> CountryResponse:
        # Создание страны с городами. Страна
        country = CountryModel(name=data.name, continent=data.continent)
        db.add(country)
        await db.flush()
        # Создаем вложенные города
        for city_data in data.cities:
            city = CityModel(name=city_data.name, country_id=country.id)
            db.add(city)
        await db.commit()
        await db.refresh(country)

        return CountryResponse.model_validate(country)

    @staticmethod
    async def get_by_id(db: AsyncSession, country_id: UUID) -> CountryResponse:
        # Получение страны по ID с вложенными городами
        query = select(CountryModel).where(CountryModel.id == country_id)
        result = await db.execute(query)
        country = result.scalar_one_or_none()

        if not country:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Country not found")

        return CountryResponse.model_validate(country)

    @staticmethod
    async def update(db: AsyncSession, country_id: UUID, data: CountryUpdate) -> CountryResponse:
        # Обновление страны и городов
        await CountryService.get_by_id(db, country_id)
        # Обновляем данные страны
        stmt = update(CountryModel).where(CountryModel.id == country_id).values(
            name=data.name,
            continent=data.continent
        )
        await db.execute(stmt)
        # Получаем страну для работы с городами
        query = select(CountryModel).where(CountryModel.id == country_id)
        result = await db.execute(query)
        country = result.scalar_one()
        # Удаляем старые города, каскадное удаление
        for city in country.cities:
            await db.delete(city)
        # Создаем новые города
        for city_data in data.cities:
            city = CityModel(name=city_data.name, country_id=country.id)
            db.add(city)

        await db.commit()
        await db.refresh(country)

        return CountryResponse.model_validate(country)

    @staticmethod
    async def delete(db: AsyncSession, country_id: UUID) -> None:
        # Удаление страны
        country = await CountryService.get_by_id(db, country_id)
        await db.delete(country)
        await db.commit()