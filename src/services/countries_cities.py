from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.services.base import BaseService
from utils.request_id import get_request_id
from src.exceptions import NotFoundError
from src.schemas.countries import CountryCreate, CountryUpdate, CountryResponse
from src.redis import redis_client
from src.repositories.country_repository import CountryRepository
import logging

logger = logging.getLogger(__name__)

class CountriesCitiesService(BaseService):
    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db
        self.request_id = get_request_id()
        self.country_repo = CountryRepository(db)

    async def create_country(self, data: CountryCreate) -> CountryResponse:
        self._log_info("Creating country", request_id=self.request_id, name=data.name, cities_count=len(data.cities))

        country = data.to_model()
        self.db.add(country)
        await self.db.refresh(country)

        self._log_info("Created country", entity_id=country.id, request_id=self.request_id)
        return CountryResponse.model_validate(country)

    async def get_country(self, country_id: UUID) -> CountryResponse:
        self._log_info("Fetching country", entity_id=country_id, request_id=self.request_id)

        cache_key = f"country:{country_id}"
        cached = await redis_client.get_cached(cache_key, CountryResponse)
        if cached:
            self._log_info("Cache HIT for country", entity_id=country_id, request_id=self.request_id)
            return cached

        self._log_info("Cache MISS for country", entity_id=country_id, request_id=self.request_id)

        country = await self.country_repo.get_with_cities(country_id)
        if not country:
            self._log_warning("Country not found", country_id=country_id, request_id=self.request_id)
            raise NotFoundError("Country", str(country_id))

        response = CountryResponse.model_validate(country)

        await redis_client.set_cached(cache_key, response)

        return response

    async def get_countries(self, skip: int = 0, limit: int = 100) -> List[CountryResponse]:
        self._log_info("Fetching countries", request_id=self.request_id, skip=skip, limit=limit)

        countries = await self.country_repo.get_all_with_relations(skip=skip, limit=limit, relations=["cities"], for_update=True)

        self._log_info("Countries fetched", count=len(countries), request_id=self.request_id)

        return CountryResponse.from_model_list(countries)

    async def update_country(self, country_id: UUID, data: CountryUpdate) -> CountryResponse:
        self._log_info("Updating country", entity_id=country_id, request_id=self.request_id)

        update_data = data.model_dump(exclude_unset=True, include={"name", "continent"})
        new_city_names = [city.name for city in data.cities] if data.add_cities else None
        country = await self.country_repo.update_country_with_cities(
            country_id,
            update_data,
            new_city_names,
        )
        if not country:
            self._log_warning("Country not found for update", entity_id=country_id, request_id=self.request_id)
            raise NotFoundError("Country", str(country_id))

        await redis_client.invalidate(f"country:{country_id}")

        self._log_info(
            "Updated country",
            entity_id=country_id,
            request_id=self.request_id,
            cities_added=len(data.add_cities) if data.add_cities else 0
        )
        return CountryResponse.model_validate(country)

    async def delete_country(self, country_id: UUID) -> None:
        self._log_info("Deleting country", entity_id=country_id, request_id=self.request_id)

        deleted = await self.country_repo.soft_delete(country_id)
        if not deleted:
            self._log_warning("Country not found for delete", entity_id=country_id, request_id=self.request_id)
            raise NotFoundError("Country", str(country_id))

        await redis_client.invalidate(f"country:{country_id}")

        self._log_info("Deleted country", entity_id=country_id, request_id=self.request_id)

