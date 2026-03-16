from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from src.exceptions import NotFoundError
from src.models.countries import CountryModel
from src.models.cities import CityModel
from src.schemas.countries import CountryCreate, CountryUpdate
from src.schemas.cities import CityCreate, CityUpdate
from src.schemas.base import StatusResponse

class CountriesCitiesService:
    @staticmethod
    async def create_country(db: AsyncSession, data: CountryCreate) -> CountryModel:
        country = CountryModel.from_schema(data)
        db.add(country)
        await db.flush()
        for city_data in data.cities:
            city = CityModel.from_schema(city_data, country.id)
            db.add(city)

        return country

    @staticmethod
    async def get_country(db: AsyncSession, country_id: UUID) -> CountryModel | None:
        query = select(CountryModel).where(CountryModel.id == country_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_country(db: AsyncSession, country_id: UUID, data: CountryUpdate) -> CountryModel:
        country = await CountriesCitiesService.get_country(db, country_id)

        if not country:
            raise NotFoundError("Country not found")

        country.name = data.name
        country.continent = data.continent

        for city in country.cities:
            await db.delete(city)

        for city_data in data.cities:
            city = CityModel.from_schema(city_data, country.id)
            db.add(city)

        return country

    @staticmethod
    async def delete_country(db: AsyncSession, country_id: UUID) -> StatusResponse:
        country = await CountriesCitiesService.get_country(db, country_id)

        if not country:
            raise NotFoundError("Country not found")

        await db.delete(country)
        return StatusResponse(status="deleted")

    @staticmethod
    async def create_city(db: AsyncSession, data: CityCreate, country_id: UUID) -> CityModel:
        country = await CountriesCitiesService.get_country(db, country_id)

        if not country:
            raise NotFoundError("Country not found")

        city = CityModel.from_schema(data, country.id)
        db.add(city)
        return city

    @staticmethod
    async def get_city(db: AsyncSession, city_id: UUID) -> CityModel |None:
        query = select(CityModel).where(CityModel.id == city_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_city(db: AsyncSession, city_id: UUID, data: CityUpdate) -> CityModel:
        city = await CountriesCitiesService.get_city(db, city_id)

        if not city:
            raise NotFoundError("City not found")

        city.name = data.name
        return city

    @staticmethod
    async def delete_city(db: AsyncSession, city_id: UUID) -> StatusResponse:
        city = await CountriesCitiesService.get_city(db, city_id)

        if not city:
            raise NotFoundError("City not found")

        await db.delete(city)
        return StatusResponse(status="deleted")