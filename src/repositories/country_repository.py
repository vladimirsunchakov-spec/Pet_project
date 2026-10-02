from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.exceptions import AlreadyExistsError, NotFoundError
from src.models.cities import CityModel
from src.models.countries import CountryModel
from src.repositories.base import BaseRepository
from src.schemas.cities import CityCreate


class CountryRepository(BaseRepository[CountryModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, CountryModel)

    async def create_country(self, country: CountryModel) -> CountryModel:
        self.db.add(country)
        await self.db.flush()
        await self.db.refresh(country)
        return country

    async def create_cities(self, cities: List[CityModel]) -> List[CityModel]:
        for city in cities:
            self.db.add(city)
        await self.db.flush()
        for city in cities:
            await self.db.refresh(city)
        return cities

    async def get_with_cities(self, country_id: UUID) -> Optional[CountryModel]:
        return await self.get_with_relations(country_id, relations=["cities"])

    async def get_existing_city_names(self, country_id: UUID, city_names: List[str]) -> set[str]:
        query = select(CityModel).where(
            CityModel.country_id == country_id,
            CityModel.name.in_(city_names),
            CityModel.is_deleted == False,
        )
        result = await self.db.execute(query)
        return {city.name for city in result.scalars().all()}

    async def add_cities_to_country(
        self,
        country_id: UUID,
        cities: List[CityCreate],
    ) -> List[CityModel]:
        country = await self.get(country_id)
        if not country:
            raise NotFoundError("Country", str(country_id))

        existing_names = await self.get_existing_city_names(
            country_id,
            [city.name for city in cities],
        )
        for city_data in cities:
            if city_data.name in existing_names:
                raise AlreadyExistsError("city", city_data.name)

        city_models = [
            CityModel(name=city.name, country_id=country.id)
            for city in cities
        ]
        return await self.create_cities(city_models)
