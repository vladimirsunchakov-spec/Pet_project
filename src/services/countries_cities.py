from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID

from src.exceptions import NotFoundError
from src.models.countries import CountryModel
from src.models.cities import CityModel
from src.schemas.countries import CountryCreate, CountryUpdate, CountryResponse
from src.schemas.cities import CityCreate, CityUpdate, CityResponse
from src.schemas.base import StatusResponse

class CountriesCitiesService:
    @staticmethod
    async def create_country(db: AsyncSession, data: CountryCreate) -> CountryResponse:
        country = CountryModel.from_schema(data)
        db.add(country)
        await db.flush()
        for city_data in data.cities:
            city = CityModel.from_schema(city_data, country_id=country.id)
            db.add(city)
        await db.commit()
        await db.refresh(country)

        return CountryResponse.model_validate(country)

    @staticmethod
    async def get_country(db: AsyncSession, country_id: UUID) -> CountryResponse:
        query = select(CountryModel).where(CountryModel.id == country_id)
        result = await db.execute(query)
        country = result.scalar_one_or_none()

        if not country:
            raise NotFoundError("Country not found")

        return CountryResponse.model_validate(country)

    @staticmethod
    async def update_country(db: AsyncSession, country_id: UUID, data: CountryUpdate) -> CountryResponse:
        query = select(CountryModel).where(CountryModel.id == country_id)
        result = await db.execute(query)
        country = result.scalar_one_or_none()

        if not country:
            raise NotFoundError("Country not found")

        country.name = data.name
        country.continent = data.continent

        for city in country.cities:
            await db.delete(city)
        for city_data in data.cities:
            city = CityModel.from_schema(city_data, country_id=country.id)
            db.add(city)

        await db.commit()
        await db.refresh(country)

        return CountryResponse.model_validate(country)

    @staticmethod
    async def delete_country(db: AsyncSession, country_id: UUID) -> None:
        query = select(CountryModel).where(CountryModel.id == country_id)
        result = await db.execute(query)
        country = result.scalar_one_or_none()

        if not country:
            raise NotFoundError("Country not found")

        await db.delete(country)
        await db.commit()

        return StatusResponse(status="deleted")

    @staticmethod
    async def get_city(db: AsyncSession, city_id: UUID) -> CityResponse:
        query = select(CityModel).where(CityModel.id == city_id)
        result = await db.execute(query)
        city = result.scalar_one_or_none()

        if not city:
            raise NotFoundError("City not found")

        return CityResponse.model_validate(city)

    @staticmethod
    async def update_city(db: AsyncSession, city_id: UUID, data: CityUpdate) -> CityResponse:
        query = select(CityModel).where(CityModel.id == city_id)
        result = await db.execute(query)
        city = result.scalar_one_or_none()

        if not city:
            raise NotFoundError("City not found")

        city.name = data.name
        await db.commit()
        await db.refresh(city)

        return CityResponse.model_validate(city)

    @staticmethod
    async def delete_city(db: AsyncSession, city_id: UUID) -> None:
        query = select(CityModel).where(CityModel.id == city_id)
        result = await db.execute(query)
        city = result.scalar_one_or_none()

        if not city:
            raise NotFoundError("City not found")

        await db.delete(city)
        await db.commit()

        return StatusResponse(status="deleted")