from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.config import Settings

settings = Settings()

# postgres_url must be like: postgresql+asyncpg://user:pass@host:port/db
engine = create_async_engine(
    str(settings.postgres_url),
    connect_args={"ssl": None},  # or False
)

SessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # prevents implicit reloads after commit (common MissingGreenlet trigger)
)


@asynccontextmanager
async def get_session() -> AsyncSession:
    async with SessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
