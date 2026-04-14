from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from src.services.base import BaseService
from src.middleware.request_id import get_request_id
from src.exceptions import NotFoundError
from src.models.countries import CountryModel
from src.models.cities import CityModel
from src.schemas.countries import CountryCreate, CountryUpdate, CountryResponse


class CountriesCitiesService(BaseService):
    def __init__(self, **kwargs):
        self.db:AsyncSession = kwargs.get("db")
        self.request_id: str = kwargs.get("request_id", get_request_id())

    async def create_country(self, **kwargs) -> CountryModel:
        data = kwargs.get("data")
        self._log_info("Creating country", request_id=self.request_id, name=data.name)

        country = CountryModel.from_schema(data)
        self.db.add(country)

        for city_data in data.cities:
            city = CityModel.from_schema(city_data, country.id)
            self.db.add(city)

        await self.db.refresh(country)

        self._log_info("Created country", entity_id=country.id, request_id=self.request_id, cities_count=len(data.cities))

        return CountryResponse.model_validate(country)

    async def get_country(self, **kwargs) -> CountryModel:
        country_id = kwargs.get("country_id")
        self._log_info("Fetching country", entity_id=country_id, request_id=self.request_id)

        query = select(CountryModel).where(CountryModel.id == country_id)
        result = await self.db.execute(query)
        country = result.scalar_one_or_none()

        if not country:
            self._log_warning("Country not found", entity_id=country_id, request_id=self.request_id)
            raise NotFoundError ("Country", str(country_id))

        return CountryResponse.model_validate(country)

    async def update_country(self, **kwargs) -> CountryModel:
        country_id = kwargs.get("country_id")
        data = kwargs.get("data")
        self._log_info("Updating country", entity_id=country_id, request_id=self.request_id)

        country = await self.get_country(country_id=country_id)

        country.name = data.name
        country.continent = data.continent

        for city in country.cities:
            await self.db.delete(city)

        for city_data in data.cities:
            city = CityModel.from_schema(city_data, country.id)
            self.db.add(city)
        await self.db.refresh(country)

        self._log_info("Updated country", entity_id=country_id, request_id=self.request_id, cities_count=len(data.cities))

        return CountryResponse.model_validate(country)

    async def delete_country(self, **kwargs) -> None:
        country_id = kwargs.get("country_id")
        self._log_info("Deleting country", entity_id=country_id, request_id=self.request_id)

        country = await self.get_country(country_id=country_id)

        await self.db.delete(country)

        self._log_info("Deleted country", entity_id=country_id, request_id=self.request_id)
