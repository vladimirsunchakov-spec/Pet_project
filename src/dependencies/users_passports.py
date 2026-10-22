from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db import get_session
from src.services.users_passports import UsersPassportsService

async def get_users_passports_service(db: AsyncSession = Depends(get_session)) -> UsersPassportsService:
    return UsersPassportsService(db)