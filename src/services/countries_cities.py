from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from src.services.base import BaseService
from src.middleware.request_id import get_request_id
from src.exceptions import NotFoundError, AlreadyExistsError
from src.models.countries import CountryModel
from src.models.cities import CityModel
from src.schemas.countries import CountryCreate, CountryUpdate, CountryResponse


class CountriesCitiesService(BaseService):
    def __init__(self, db: AsyncSession):
        self.db:AsyncSession = db
        self.request_id = get_request_id()

    async def create_country(self, data: CountryCreate) -> CountryResponse:
        self._log_info("Creating country", request_id=self.request_id, name=data.name)

        country = data.to_model()
        self.db.add(country)

        await self.db.refresh(country)

        self._log_info("Created country", entity_id=country.id, request_id=self.request_id, cities_count=len(data.cities))

        return CountryResponse.model_validate(country)

    async def get_country(self, country_id: UUID) -> CountryResponse:
        self._log_info("Fetching country", entity_id=country_id, request_id=self.request_id)

        query = select(CountryModel).where(CountryModel.id == country_id)
        result = await self.db.execute(query)
        country = result.scalar_one_or_none()

        if not country:
            self._log_warning("Country not found", entity_id=country_id, request_id=self.request_id)
            raise NotFoundError("Country", str(country_id))

        return CountryResponse.model_validate(country)

    async def update_country(self, country_id: UUID, data: CountryUpdate) -> CountryResponse:
        self._log_info("Updating country", entity_id=country_id, request_id=self.request_id)

        country = await self.get_country(country_id)
        data.update_model(country)

        if data.add_cities:
            existing_names = {city.name for city in country.cities}
            for city_data in data.add_cities:
                if city_data.name in existing_names:
                    self._log_error(f"City '{city_data.name}' already exists in country", entity_id=country_id, request_id=self.request_id)
                    raise AlreadyExistsError("City", city_data.name)

            new_cities = [city_data.to_model(country) for city_data in data.add_cities]
            self.db.add_all(new_cities)

        await self.db.refresh(country)

        self._log_info("Updated country", entity_id=country_id, request_id=self.request_id, cities_count=len(data.cities))
        return CountryResponse.model_validate(country)

    async def delete_country(self, country_id: UUID) -> None:
        self._log_info("Deleting country", entity_id=country_id, request_id=self.request_id)

        country = await self.get_country(country_id=country_id)
        await self.db.delete(country)

        self._log_info("Deleted country", entity_id=country_id, request_id=self.request_id)
