from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models.countries import CountryModel
from src.repositories.base import BaseRepository

class CountryRepository(BaseRepository[CountryModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, CountryModel)

    async def get_with_cities(self, id: UUID) -> Optional[CountryModel]:
        query = (
            select(CountryModel)
            .where(CountryModel.id == id, CountryModel.is_deleted == False)
            .options(selectinload(CountryModel.cities))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def get_all_with_cities_query(self, skip: int = 0, limit: int = 100) -> Select:
        return (
            select(CountryModel)
            .where(CountryModel.is_deleted == False)
            .offset(skip)
            .limit(limit)
            .options(selectinload(CountryModel.cities))
        )

    async def get_all_with_cities(self, skip: int = 0, limit: int = 100) -> List[CountryModel]:
        query = self.get_all_with_cities_query(skip, limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

