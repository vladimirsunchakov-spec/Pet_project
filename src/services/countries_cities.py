from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.models.cities import CityModel
from src.schemas.cities import CityResponse, CityCreate
from src.services.base import BaseService
from utils.request_id import get_request_id
from src.exceptions import NotFoundError
from src.schemas.countries import CountryCreate, CountryUpdate, CountryResponse
from src.redis_client import redis_client
from src.repositories.country_repository import CountryRepository
import logging

logger = logging.getLogger(__name__)

class CountriesCitiesService(BaseService):
    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db
        self.request_id = get_request_id()
        self.country_repo = CountryRepository(db)

    async def create_country(self, data: CountryCreate) -> CountryResponse:
        country = data.to_model()
        created = await self.country_repo.create_country(country)

        if data.cities:
            city_models = [
                CityModel(name=city.name, country_id=created.id)
                for city in data.cities
            ]
            await self.country_repo.create_cities(city_models)
        logger.info(
        "Created country",
            extra={
                "entity_id": str(created.id),
                "name": created.name,
                "cities_count": len(data.cities),
                "request_id": self.request_id
            }
        )
        return CountryResponse.model_validate(created)

    async def get_country(self, country_id: UUID) -> CountryResponse:
        cache_key = f"country:{country_id}"
        cached = await redis_client.get_cached(cache_key, CountryResponse)
        if cached:
            return cached

        country = await self.country_repo.get_with_cities(country_id)
        if not country:
            logger.warning(
                "Country not found",
                extra={"country_id": str(country_id), "request_id": self.request_id}
            )
            raise NotFoundError("Country", str(country_id))

        response = CountryResponse.model_validate(country)

        await redis_client.set_cached(cache_key, response)

        logger.info("Country fetched", extra={"country_id": str(country_id), "request_id": self.request_id})

        return response

    async def get_countries(self, skip: int = 0, limit: int = 100) -> List[CountryResponse]:
        countries = await self.country_repo.get_all_with_relations(skip=skip, limit=limit, relations=["cities"])

        logger.info("Countries fetched", extra={"count": len(countries), "request_id": self.request_id})

        return CountryResponse.from_model_list(countries)

    async def update_country(self, country_id: UUID, data: CountryUpdate) -> CountryResponse:
        country = await self.country_repo.get_with_cities(country_id)
        if not country:
            logger.warning(
                "Country not found for update",
                extra={"country_id": str(country_id), "request_id": self.request_id}
            )
            raise NotFoundError("Country", str(country_id))

        update_data = data.model_dump(exclude_unset=True, include={"name", "continent"})
        for key, value in update_data.items():
            if value is not None:
                setattr(country, key, value)

        updated = await self.country_repo.update(country_id, **update_data)
        await redis_client.invalidate(f"country:{country_id}")

        logger.info(
            "Updated country",
            extra={"entity_id": str(country_id), "request_id": self.request_id}
        )

        return CountryResponse.model_validate(updated)

    async def add_city_to_country(self, country_id: UUID, cities: List[CityCreate]) -> List[CityResponse]:
        country = await self.country_repo.get(country_id)
        if not country:
            raise NotFoundError("Country", str(country_id))

        existing_names = await self.country_repo.get_existing_city_names(
            country_id,
            [city.name for city in cities]
        )
        new_cities = []
        for city_data in cities:
            if city_data.name not in existing_names:
                city_model = CityModel(
                    name=city_data.name,
                    country_id=country.id,
                )
                new_cities.append(city_model)

        if new_cities:
            created_cities = await self.country_repo.create_cities(new_cities)
        else:
            created_cities = []

        logger.info(
            "Cities added to country",
            extra={"entity_id": str(country_id), "cities_added": len(new_cities), "request_id": self.request_id}
        )
        return [CityResponse.model_validate(city) for city in created_cities]

    async def delete_country(self, country_id: UUID) -> None:
        deleted = await self.country_repo.soft_delete(country_id)
        if not deleted:
            logger.warning("Country not found for delete", extra={"country_id": str(country_id), "request_id": self.request_id})
            raise NotFoundError("Country", str(country_id))

        await redis_client.invalidate(f"country:{country_id}")

        logger.info("Deleted country", extra={"entity_id": str(country_id), "request_id": self.request_id})

