from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID

from src.exceptions import NotFoundError

from src.models.countries import CountryModel
from src.models.cities import CityModel
from src.schemas.countries import CountryCreate, CountryUpdate, CountryResponse

class CountryService:
    @staticmethod
    async def create(db: AsyncSession, data: CountryCreate) -> CountryResponse:
        # Создание страны с городами. Страна
        country = CountryModel.from_schema(data)
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
            raise NotFoundError("Country not found")

        return CountryResponse.model_validate(country)

    @staticmethod
    async def update(db: AsyncSession, country_id: UUID, data: CountryUpdate) -> CountryResponse:
        query = select(CountryModel).where(CountryModel.id == country_id)
        result = await db.execute(query)
        country = result.scalar_one_or_none()

        if not country:
            raise NotFoundError("Country not found")

        country.name = data.name
        country.continent = data.continent

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