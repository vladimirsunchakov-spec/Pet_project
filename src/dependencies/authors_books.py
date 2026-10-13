from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db import get_session
from src.services.authors_books import AuthorsBooksService


async def get_authors_books_service(
    db: AsyncSession = Depends(get_session),
) -> AuthorsBooksService:
    return AuthorsBooksService(db)
