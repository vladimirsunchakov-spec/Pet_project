from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from fastapi import HTTPException, status

from src.models.cities import CityModel
from src.models.countries import CountryModel
from src.schemas.cities import CityCreate, CityUpdate, CityResponse

class CityService:
    @staticmethod
    async def create(db: AsyncSession, data: CityCreate, country_id: UUID) -> CityResponse:
        # Создание города в какой-то стране
        # Проверяем, что страна существует
        query = select(CountryModel).where(CountryModel.id == country_id)
        result = await db.execute(query)
        country = result.scalar_one_or_none()

        if not country:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Country not found")
        # Создаем город
        city = CityModel(name=data.name, country_id=country_id)
        db.add(city)
        await db.commit()
        await db.refresh(city)

        return CityResponse.model_validate(city)

    @staticmethod
    async def get_by_id(db: AsyncSession, city_id: UUID) -> CityResponse:
        # Получение города по ID
        query = select(CityModel).where(CityModel.id == city_id)
        result = await db.execute(query)
        city = result.scalar_one_or_none()

        if not city:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="City not found")

        return CityResponse.model_validate(city)

    @staticmethod
    async def update(db: AsyncSession, city_id: UUID, data: CityUpdate) -> CityResponse:
        # Обновление города
        await CityService.get_by_id(db, city_id)

        stmt = update(CityModel).where(CityModel.id == city_id).values(name=data.name)
        await db.execute(stmt)
        await db.commit()

        return await CityService.get_by_id(db, city_id)

    @staticmethod
    async def delete(db: AsyncSession, city_id: UUID) -> None:
        # Удаление города
        city = await CityService.get_by_id(db, city_id)
        await db.delete(city)
        await db.commit()