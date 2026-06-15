from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from service2.src2.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()