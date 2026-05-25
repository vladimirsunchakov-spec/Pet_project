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

        query = (select(CountryModel)
                 .where(CountryModel.id == country_id, CountryModel.is_deleted == False)
                 .options(selectinload(CountryModel.cities)))
        result = await self.db.execute(query)
        country = result.scalar_one_or_none()

        if not country:
            self._log_warning("Country not found", entity_id=country_id, request_id=self.request_id)
            raise NotFoundError("Country", str(country_id))

        return CountryResponse.model_validate(country)

    async def get_countries(self, skip: int = 0, limit: int = 100) -> List[CountryResponse]:
        self._log_info("Fetching countries",request_id=self.request_id, skip=skip, limit=limit)

        query = (
            select(CountryModel)
            .where(CountryModel.is_deleted == False)
            .offset(skip)
            .limit(limit)
            .options(selectinload(CountryModel.cities))
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(query)
        countries = result.scalars().all()

        return CountryResponse.from_model_list(countries)

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

        stmt = (update(CountryModel).where(CountryModel.id == country_id).values(is_deleted=True, deleted_at=datetime.now(timezone.utc)))
        await self.db.execute(stmt)
        self._log_info("Deleted country", entity_id=country_id, request_id=self.request_id)
