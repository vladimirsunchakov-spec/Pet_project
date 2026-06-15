from datetime import timezone, datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from uuid import UUID
from src.services.base import BaseService
from src.middleware.request_id import get_request_id
from src.exceptions import NotFoundError, AlreadyExistsError
from src.models.countries import CountryModel
from src.schemas.countries import CountryCreate, CountryUpdate, CountryResponse
from src.core.redis import redis_client
from src.repositories.country_repository import CountryRepository

class CountriesCitiesService(BaseService):
    def __init__(self, db: AsyncSession):
        self.db:AsyncSession = db
        self.request_id = get_request_id()
        self.country_repo = CountryRepository(db)

    async def create_country(self, data: CountryCreate) -> CountryResponse:
        self._log_info("Creating country", request_id=self.request_id, name=data.name, cities_count=len(data.cities))

        country = data.to_model()
        self.db.add(country)
        self._log_info("Created country", entity_id=country.id, request_id=self.request_id)
        return CountryResponse.model_validate(country)

    async def get_country(self, country_id: UUID) -> CountryResponse:
        self._log_info("Fetching country", entity_id=country_id, request_id=self.request_id)

        cache_key = f"country:{country_id}"
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            self._log_info("Cached HIT for country", entity_id=country_id, request_id=self.request_id)
            return CountryResponse.model_validate(cached_data)

        self._log_info("Cached MISS for country", entity_id=country_id, request_id=self.request_id)

        country = await self.country_repo.get_with_cities(country_id)
        if not country:
            self._log_warning("Country not found", country_id=country_id, request_id=self.request_id)
            raise NotFoundError("Country", str(country_id))

        response = CountryResponse.model_validate(country)
        await redis_client.set(cache_key, response.model_dump(), ttl=3600)
        self._log_info("Country cached", entity_id=country_id, request_id=self.request_id)

        return response

    async def get_countries(self, skip: int = 0, limit: int = 100) -> List[CountryResponse]:
        self._log_info("Fetching countries",request_id=self.request_id, skip=skip, limit=limit)

        query = self.country_repo.get_all_with_cities_query(skip, limit)
        query = query.with_for_update(skip_locked=True)
        result = await self.db.execute(query)
        countries = result.scalars().all()

        self._log_info("Countries fetched", count=len(countries), request_id=self.request_id)

        return CountryResponse.from_model_list(countries)

    async def update_country(self, country_id: UUID, data: CountryUpdate) -> CountryResponse:
        self._log_info("Updating country", entity_id=country_id, request_id=self.request_id)

        country = await self.country_repo.get_with_cities(country_id)
        if not country:
            self._log_warning("Country not found for update", entity_id=country_id, request_id=self.request_id)
            raise NotFoundError("Country", str(country_id))

        data.update_model(country)

        if data.add_cities:
            existing_names = {city.name for city in country.cities}
            for city_data in data.add_cities:
                if city_data.name in existing_names:
                    self._log_error(f"City '{city_data.name}' already exists in country", country_id=country_id, request_id=self.request_id)
                    raise AlreadyExistsError("City", city_data.name)

            new_cities = [city_data.to_model(country) for city_data in data.add_cities]
            self.db.add_all(new_cities)

        await redis_client.delete(f"country:{country_id}")

        self._log_info("Cache invalidate for country", country_id=country_id, request_id=self.request_id)
        self._log_info("Updated country", entity_id=country_id, request_id=self.request_id, cities_count=len(data.cities))
        return CountryResponse.model_validate(country)

    async def delete_country(self, country_id: UUID) -> None:
        self._log_info("Deleting country", entity_id=country_id, request_id=self.request_id)

        deleted = await self.country_repo.soft_delete(country_id)
        if not deleted:
            self._log_warning("Country not found for deleted", entity_id=country_id, request_id=self.request_id)
            raise NotFoundError("Country", str(country_id))

        await redis_client.delete(f"country:{country_id}")
        self._log_info("Cache invalidate for deleted country", country_id=country_id, request_id=self.request_id)
        self._log_info("Deleted country", entity_id=country_id, request_id=self.request_id)

