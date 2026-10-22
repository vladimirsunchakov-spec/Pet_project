from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db import get_session
from src.services.countries_cities import CountriesCitiesService

async def get_countries_cities_service(db: AsyncSession = Depends(get_session)) -> CountriesCitiesService:
    return CountriesCitiesService(db)
