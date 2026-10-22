from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Dict
from src.config import settings
from src.db import get_session
from src.application import get_app
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
import logging
from redis import asyncio as redis

logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:14") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7") as container:
        yield container

@pytest_asyncio.fixture(scope="session")
async def test_engine(postgres_container):
    database_url = postgres_container.get_connection_url()
    async_database_url = database_url.replace("postgres://", "postgresql+asyncpg://")

    engine = create_async_engine(async_database_url, echo=False, future=True,)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with async_session_maker() as session:
        yield session

@pytest_asyncio.fixture
async def redis_client(redis_container):
    client = redis.from_url(
        redis_container.get_connection_url(),
        decode_responses=True,
    )
    await client.ping()
    yield client
    await client.close()

@pytest_asyncio.fixture
async def client(db_session, redis_client):
    app = get_app()

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def http_client():
    async with AsyncClient() as client:
        yield client

@pytest.fixture
def test_author_data() -> Dict:
    return {
        "name": "Test Author",
        "rating": 4.5,
        "awards_count": 3,
    }

@pytest.fixture
def test_bio_data() -> Dict:
    return {
        "rating": 4.5,
        "awards_count": 3,
        "biography": "Test Biography",
    }

@pytest_asyncio.fixture
async def clean_tables(db_session):
    yield
    for table in reversed(db_session.get_bind()._all_tables):
        await db_session.execute(table.delete())
    await db_session.commit()

def pytest_configure(config):
    config.option.async_mode = "auto"
    logger.info("Pytest configured with async_mode=auto")