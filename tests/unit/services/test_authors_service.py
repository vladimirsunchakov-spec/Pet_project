
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
import pytest
from uuid import uuid4
from datetime import date

from poetry.console.commands import self

from src.services.authors_books import AuthorsBooksService
from src.schemas.authors import AuthorCreate, AuthorUpdate, BookSchema
from src.exceptions import NotFoundError

@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.get_with_books = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.soft_delete = AsyncMock()
    repo.get_all_with_books = AsyncMock()
    repo.get_all_with_books_query = MagicMock()
    return repo

@pytest.fixture
def mock_bio_client():
    client = AsyncMock()
    client.create_bio = AsyncMock()
    client.get_bio_by_author_id = AsyncMock()
    client.delete_bio = AsyncMock()
    return client

@pytest.fixture
def service(mock_repo, mock_bio_client):
    with patch('src.services.authors_books.redis_client') as mock_redis:
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()
        mock_redis.delete = AsyncMock()

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        service = AuthorsBooksService(mock_db)
        service.author_repo = mock_repo
        service.bio_client = mock_bio_client
        yield service

@pytest.mark.asyncio
async def test_create_author_success(service, mock_repo, mock_bio_client):
    author_id = uuid4()

    data = AuthorCreate(
        name="Test Author",
        books=[BookSchema(title="Test Book")],
        birth_date=date(1990, 1, 1),
        country="Test Country"
    )
    mock_author = MagicMock()
    mock_author.id = author_id
    mock_repo.create = AsyncMock(return_value=mock_author)
    mock_bio_client.create_bio = AsyncMock(return_value={"id": str(uuid4())})

    with patch('src.schemas.authors.AuthorResponse.model_validate') as mock_validate:
        mock_response = MagicMock()
        mock_response.name = "Test Author"
        mock_validate.return_value = mock_response

        result = await service.create_author(data)

    assert result.name == "Test Author"

@pytest.mark.asyncio
async def test_get_author_success(service, mock_repo, mock_bio_client):
    author_id = uuid4()
    mock_author = MagicMock()
    mock_author.id = author_id
    mock_author.name = "Test Author"
    mock_repo.get_with_books.return_value = mock_author

    mock_bio_client.get_bio__by_author_id.return_value = {
        "rating": 4.5,
        "awards_count": 10
    }
    with patch('src.schemas.authors.AuthorResponse.model_validate') as mock_validate:
        mock_response = MagicMock()
        mock_response.id = author_id
        mock_response.name = "Test Author"
        type(mock_response).rating = PropertyMock(return_value=4.5)
        type(mock_response).awards_count = PropertyMock(return_value=10)
        mock_validate.return_value = mock_response

        result = await service.get_author(author_id)

    assert result.id == author_id
    assert result.name == "Test Author"
    assert result.rating == 4.5
    assert result.awards_count == 10

@pytest.mark.asyncio
async def test_get_author_not_found(service, mock_repo):
    author_id = uuid4()
    mock_repo.get_with_books.return_value = None

    with pytest.raises(NotFoundError):
        await service.get_author(author_id)

@pytest.mark.asyncio
async def test_author_no_bio_data(service, mock_repo, mock_bio_client):
    author_id = uuid4()
    mock_author = MagicMock()
    mock_author.id = author_id
    mock_author.name = "Test Author"
    mock_author.books = []
    mock_repo.get_with_books.return_value = mock_author
    mock_bio_client.get_bio_by_author_id.return_value = None

    with patch('src.schemas.authors.AuthorResponse.model_validate') as mock_validate:
        mock_response = MagicMock()
        mock_response.id = author_id
        mock_response.name = "Test Author"
        mock_response.books = []
        mock_response.rating = None
        mock_response.awards_count = None
        mock_validate.return_value = mock_response

        result = await service.get_author(author_id)

    assert result.rating is None
    assert result.awards_count is None

@pytest.mark.asyncio
async def test_update_author_success(service, mock_repo):
    author_id = uuid4()
    mock_author = MagicMock()
    mock_author.id = author_id
    mock_author.name = "Old Author"
    mock_author.country = "Old Country"

    mock_repo.get_with_books.return_value = mock_author

    data = AuthorUpdate(
        name="New Name",
        country="New Country",
    )
    mock_response = MagicMock()
    mock_response.name = "New Name"
    mock_response.country = "New Country"

    with patch("src.schemas.authors.AuthorResponse.model_validate", return_value=mock_response):
        result = await service.update_author(author_id, data)

    mock_repo.get_with_books.assert_called_once_with(author_id)

    assert result.name == "New Name"
    assert result.country == "New Country"

@pytest.mark.asyncio
async def test_update_author_not_found(service, mock_repo):
    author_id = uuid4()
    mock_repo.get_with_books.return_value = None

    data = AuthorUpdate(name="New Name")

    with pytest.raises(NotFoundError):
        await service.update_author(author_id, data)

@pytest.mark.asyncio
async def test_delete_author_success(service, mock_repo, mock_bio_client):
    author_id = uuid4()
    mock_repo.soft_delete.return_value = True

    await service.delete_author(author_id)

    mock_repo.soft_delete.assert_called_once_with(author_id)
    mock_bio_client.delete_bio.assert_called_once_with(author_id)

@pytest.mark.asyncio
async def test_delete_author_not_found(service, mock_repo):
    author_id = uuid4()
    mock_repo.soft_delete.return_value = False

    with pytest.raises(NotFoundError):
        await service.delete_author(author_id)

@pytest.mark.asyncio
async def test_author_get_list(service, mock_repo):

    mock_authors = []
    for i in range(3):
        mock_author = MagicMock()
        mock_author.id = uuid4()
        mock_author.name = f"Test Author {i}"
        mock_author.books = []
        mock_author.birth_date = date(1990, 1, 1)
        mock_author.country = "Test Country"
        mock_authors.append(mock_author)

    mock_repo.get_all_with_books_for_update = AsyncMock(return_value=mock_authors)

    with patch('src.schemas.authors.AuthorResponse.model_validate') as mock_validate:
        def validation_side_effect(model):
            mock_response = MagicMock()
            mock_response.id = model.id
            mock_response.name = model.name
            mock_response.books = model.books
            mock_response.birth_date = model.birth_date
            mock_response.country = model.country
            return mock_response

        mock_validate.side_effect = validation_side_effect

        result = await service.get_authors(skip=0, limit=10)

    assert len(result) == 3
    mock_repo.get_all_with_books_for_update.assert_called_once_with(skip=0, limit=10, request_id=service.request_id)





