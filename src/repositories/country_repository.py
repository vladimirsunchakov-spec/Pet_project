from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models.cities import CityModel
from src.models.countries import CountryModel
from src.repositories.base import BaseRepository

class CountryRepository(BaseRepository[CountryModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, CountryModel)

    async def get_with_relations(
            self,
            id: UUID,
            relations: Optional[List[str]] = None
    ) -> Optional[CountryModel]:
        query = select(CountryModel).where(CountryModel.id == id, CountryModel.is_deleted == False)

        if relations:
            options = [selectinload(getattr(CountryModel, rel)) for rel in relations]
            query = query.options(*options)

        result = await self.db.execute(query)
        country = result.scalar_one_or_none()
        return country

    async def get_with_cities(self, id: UUID) -> Optional[CountryModel]:
        return await self.get_with_relations(id, relations=["cities"])

    async def get_all_with_relations(
        self,
        skip: int = 0,
        limit: int = 100,
        relations: Optional[List[str]] = None,
    ) -> List[CountryModel]:
        query = select(CountryModel).where(CountryModel.is_deleted == False)

        if relations:
            options = [selectinload(getattr(CountryModel, rel)) for rel in relations]
            query = query.options(*options)

        query = query.offset(skip).limit(limit)
        query = query.with_for_update(skip_locked=True)
        result = await self.db.execute(query)
        countries = list(result.scalars().all())
        return countries

    async def city_exists_in_country(self, city_name: str, country_id: UUID) -> bool:
        query = select(CityModel).where(
            CityModel.name == city_name,
            CityModel.country_id == country_id,
            CityModel.is_deleted == False
        )
        result = await self.db.execute(query)
        exists = result.scalar_one_or_none() is not None

    async def add_cities_if_not_exist(
            self,
            country_id: UUID,
            city_names: List[str],
    ) -> List[CountryModel]:

        query = select(CityModel).where(
            CityModel.country_id == country_id,
            CityModel.name.in_(city_names),
            CityModel.is_deleted == False
        )
        result = await self.db.execute(query)
        existing_names = {city.name for city in result.scalars().all()}
        new_cities = []
        for name in city_names:
            if name  not in existing_names:
                city = CityModel(name=name, country_id=country_id)
                self.db.add(city)
                new_cities.append(city)

        return new_cities

    async def update_country_with_cities(
            self,
            country_id: UUID,
            update_data: dict,
            new_cities_names: Optional[List[str]] = None
    ) -> CountryModel:
        query = select(CountryModel).where(
            CountryModel.id == country_id,
            CountryModel.is_deleted == False
        ).with_for_update(skip_locked=True)
        result = await self.db.execute(query)
        country = result.scalar_one_or_none()

        if not country:
            return None

        for key, value in update_data.items():
            if value is not None:
                setattr(country, key, value)

        if new_cities_names:
            query = select(CityModel).where(
                CityModel.country_id == country_id,
                CityModel.name.in_(new_cities_names),
                CityModel.is_deleted == False
            )
            result = await self.db.execute(query)
            existing_names = {city.name for city in result.scalars().all()}

            for name in new_cities_names:
                if name not in existing_names:
                    city = CityModel(name=name, country_id=country_id)
                    self.db.add(city)
            return country



