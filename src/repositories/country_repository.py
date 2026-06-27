from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models.cities import CityModel
from src.models.countries import CountryModel
from src.repositories.base import BaseRepository
import logging

logger = logging.getLogger(__name__)

class CountryRepository(BaseRepository[CountryModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, CountryModel)

    async def get_with_relations(
            self,
            id: UUID,
            relations: Optional[List[str]] = None
    ) -> Optional[CountryModel]:
        logger.info(f"Getting country {id} with relations {relations}")
        query = select(CountryModel).where(CountryModel.id == id, CountryModel.is_deleted == False)

        if relations:
            options = [selectinload(getattr(CountryModel, rel)) for rel in relations]
            query = query.options(*options)

        result = await self.db.execute(query)
        country = result.scalar_one_or_none()
        if country:
            logger.info(f"Country {id} found")
        else:
            logger.warning(f"Country {id} not found")
        return country

    async def get_with_cities(self, id: UUID) -> Optional[CountryModel]:
        return await self.get_with_relations(id, relations=["cities"])

    async def get_all_with_relations(
        self,
        skip: int = 0,
        limit: int = 100,
        relations: Optional[List[str]] = None,
        for_update: bool = False
    ) -> List[CountryModel]:
        logger.info(f"Getting all countries with relations {relations}, skip {skip}, limit {limit}, for_update={for_update}")

        query = select(CountryModel).where(CountryModel.is_deleted == False)

        if relations:
            options = [selectinload(getattr(CountryModel, rel)) for rel in relations]
            query = query.options(*options)

        query = query.offset(skip).limit(limit)

        if for_update:
            query = query.with_for_update(skip_locked=True)

        result = await self.db.execute(query)
        countries = list(result.scalars().all())
        logger.info(f"Retrieved {len(countries)} countries")
        return countries

    async def get_all_with_cities_for_update(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CountryModel]:
        return await self.get_all_with_relations(skip, limit, relations=["cities"], for_update=True)

    async def city_exists_in_country(self, city_name: str, country_id: UUID) -> bool:
        query = select(CityModel).where(
            CityModel.name == city_name,
            CityModel.country_id == country_id,
            CityModel.is_deleted == False
        )
        result = await self.db.execute(query)
        exists = result.scalar_one_or_none() is not None
        logger.info(f"City '{city_name}' exists in country {country_id}: {exists}")

