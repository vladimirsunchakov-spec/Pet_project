import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from fastapi.testclient import TestClient
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.models import authors, books, author_book, countries, cities, users, passports
import pytest
from src.models.base import Base
from src.application import get_app
from src.db import get_session
from unittest.mock import AsyncMock, MagicMock, patch

def pytest_configure(config):
    config.option.async_mode = "auto"

@pytest.fixture
def mock_redis():
    with patch("src.core.redis.redis_client") as mock:
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock()
        mock.delete = AsyncMock()
        yield mock

@pytest.fixture
def mock_bio_client():
    with patch("src.clients.bio_client.BioServiceClient") as MockBioClient:
        mock_instance = AsyncMock()
        mock_instance.get_bio_by_author_id = AsyncMock(return_value=None)
        mock_instance.create_bio = AsyncMock(return_value={"id": "test-bio-id"})
        mock_instance.update_bio = AsyncMock(return_value=None)
        mock_instance.delete_bio = AsyncMock(return_value=None)
        MockBioClient.return_value = mock_instance
        yield MockBioClient


@pytest.fixture
async def db_session():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')

    async with engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

    await engine.dispose()

@pytest.fixture
async def client(db_session):
    app = get_app()

    async def mock_get_session():
        return AsyncMock()

    app.dependency_overrides[get_session] = mock_get_session

    return TestClient(app)
