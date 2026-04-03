from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from src.services.base import BaseService
from src.middleware.request_id import get_request_id
from src.exceptions import NotFoundError
from src.models.countries import CountryModel
from src.models.cities import CityModel
from src.schemas.countries import CountryCreate, CountryUpdate
from src.schemas.cities import CityCreate, CityUpdate

class CountriesCitiesService(BaseService):
    @classmethod
    async def create_country(cls, **kwargs) -> CountryModel:
        db = kwargs.get("db")
        data = kwargs.get("data")
        request_id = kwargs.get("request_id")

        cls._log_info("Creating country", request_id=request_id, name=data.name)

        country = CountryModel.from_schema(data)
        db.add(country)
        await db.flush()

        for city_data in data.cities:
            city = CityModel.from_schema(city_data, country.id)
            db.add(city)
        await db.refresh(country)

        cls._log_info("Created country", entity_id=country.id, request_id=request_id, cities_count=len(data.cities))

        return country

    @classmethod
    async def get_country(cls, **kwargs) -> CountryModel | None:
        db = kwargs.get("db")
        country_id = kwargs.get("country_id")
        request_id = kwargs.get("request_id", get_request_id())

        cls._log_info("Fetching country", entity_id=country_id, request_id=request_id)

        query = select(CountryModel).where(CountryModel.id == country_id)
        result = await db.execute(query)
        country = result.scalar_one_or_none()

        if not country:
            cls._log_warning("Country not found", entity_id=country_id, request_id=request_id)

        return country

    @classmethod
    async def update_country(cls, **kwargs) -> CountryModel:
        db = kwargs.get("db")
        country_id = kwargs.get("country_id")
        data = kwargs.get("data")
        request_id = kwargs.get("request_id", get_request_id())

        cls._log_info("Updating country", entity_id=country_id, request_id=request_id)

        country = await cls.get_country(db=db, country_id=country_id, request_id=request_id)
        if not country:
            cls._log_error("Country not found for update", entity_id=country_id, request_id=request_id)
            raise NotFoundError("Country", str(country_id))

        country.name = data.name
        country.continent = data.continent

        for city in country.cities:
            await db.delete(city)

        for city_data in data.cities:
            city = CityModel.from_schema(city_data, country.id)
            db.add(city)
        await db.refresh(country)

        cls._log_info("Updated country", entity_id=country_id, request_id=request_id, cities_count=len(data.cities))

        return country

    @classmethod
    async def delete_country(cls, **kwargs) -> None:
        db = kwargs.get("db")
        country_id = kwargs.get("country_id")
        request_id = kwargs.get("request_id", get_request_id())

        cls._log_info("Deleting country", entity_id=country_id, request_id=request_id)

        country = await cls.get_country(db=db, country_id=country_id, request_id=request_id)
        if not country:
            cls._log_error("Country not found", entity_id=country_id, request_id=request_id)
            raise NotFoundError("Country", str(country_id))

        await db.delete(country)

        cls._log_info("Deleted country", entity_id=country_id, request_id=request_id)

    @classmethod
    async def create_city(cls, **kwargs) -> CityModel:
        db = kwargs.get("db")
        data = kwargs.get("data")
        country_id = kwargs.get("country_id")
        request_id = kwargs.get("request_id", get_request_id())

        cls._log_info("Creating city", request_id=request_id, name=data.name, country_id=str(country_id))

        country = await cls.get_country(db=db, country_id=country_id, request_id=request_id)
        if not country:
            cls._log_error("Country not found for city creation", entity_id=country_id, request_id=request_id)
            raise NotFoundError("Country", str(country_id))

        city = CityModel.from_schema(data, country.id)
        db.add(city)
        await db.refresh(country)

        cls._log_info("City created", entity_id=city.id, request_id=request_id)

        return city

    @classmethod
    async def get_city(cls, **kwargs) -> CityModel | None:
        db = kwargs.get("db")
        city_id = kwargs.get("city_id")
        request_id = kwargs.get("request_id", get_request_id())

        cls._log_info("Fetching city", entity_id=city_id, request_id=request_id)

        query = select(CityModel).where(CityModel.id == city_id)
        result = await db.execute(query)
        city = result.scalar_one_or_none()

        if not city:
            cls._log_warning("City not found", entity_id=city_id, request_id=request_id)

        return city

    @classmethod
    async def update_city(cls, **kwargs) -> CityModel:
        db = kwargs.get("db")
        city_id = kwargs.get("city_id")
        data = kwargs.get("data")
        request_id = kwargs.get("request_id", get_request_id())

        cls._log_info("Updating city", entity_id=city_id, request_id=request_id)

        city = await cls.get_city(db=db, city_id=city_id, request_id=request_id)
        if not city:
            cls._log_error("City not found for update", entity_id=city_id, request_id=request_id)
            raise NotFoundError("City", str(city_id))

        city.name = data.name
        await db.refresh(city)

        cls._log_info("Updated city", entity_id=city.id, request_id=request_id)

        return city

    @classmethod
    async def delete_city(cls, **kwargs) -> None:
        db = kwargs.get("db")
        city_id = kwargs.get("city_id")
        request_id = kwargs.get("request_id", get_request_id())

        cls._log_info("Deleting city", entity_id=city_id, request_id=request_id)

        city = await cls.get_city(db=db, city_id=city_id, request_id=request_id)

        if not city:
            cls._log_error("City not found for deletion", entity_id=city_id, request_id=request_id)
            raise NotFoundError("City", str(city_id))

        await db.delete(city)

        cls._log_info("Deleted city", entity_id=city.id, request_id=request_id)
