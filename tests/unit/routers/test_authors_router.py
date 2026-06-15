import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import date
from fastapi.testclient import TestClient
from src.application import get_app
from src.schemas.authors import AuthorResponse, BookSchema
from src.exceptions import NotFoundError
from src.db import get_session

@pytest.fixture
def client():
    with patch('src.routers.authors_books.AuthorsBooksService') as MockService:
        mock_service = AsyncMock()
        MockService.return_value = mock_service

        app = get_app()

        async def mock_get_session():
            yield AsyncMock()

        app.dependency_overrides[get_session] = mock_get_session

        yield TestClient(app), mock_service

def test_create_author_success(client):
    test_client, mock_service = client
    author_id = uuid4()

    expected_response = AuthorResponse(
        id=author_id,
        name="Test Author",
        books=[BookSchema(title="Test Book")],
        birth_date=date(1990, 1, 1),
        country="Test Country"
    )
    mock_service.create_author.return_value = expected_response

    response = test_client.post(
        "/v1/authors-books/",
        json={
            "name": "Test Author",
            "books": [{"title": "Test Book"}],
            "birth_date": "1990-01-01",
            "country": "Test Country"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Author"
    assert data["id"] == str(author_id)

def test_create_author_missing_name(client):
    test_client, _ = client

    response = test_client.post(
        "/v1/authors-books/",
        json={
            "books": [{"title": "Test Book"}],
            "birth_date": "1990-01-01",
            "country": "Test Country"
        }
    )
    assert response.status_code == 422

def test_create_author_empty_books(client):
    test_client, _ = client
    response = test_client.post(
        "/v1/authors-books/",
        json={
            "name": "Test Author",
            "books": [],
            "birth_date": "1990-01-01",
            "country": "Test Country"
        }
    )
    assert response.status_code == 422

def test_get_author_success(client):
    test_client, mock_service = client
    author_id = uuid4()

    expected_response = AuthorResponse(
        id=author_id,
        name="Test Author",
        books=[BookSchema(title="Test Book")],
        birth_date=date(1990, 1, 1),
        country="Test Country"
    )
    mock_service.get_author.return_value = expected_response

    response = test_client.get(f"/v1/authors-books/{author_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(author_id)
    assert data["name"] == "Test Author"

def test_get_author_not_found(client):
    test_client, mock_service = client
    author_id = uuid4()

    mock_service.get_author.side_effect = NotFoundError("Author", str(author_id))

    response = test_client.get(f"/v1/authors-books/{author_id}")

    assert response.status_code == 404

def test_update_author_success(client):
    test_client, mock_service = client
    author_id = uuid4()

    expected_response = AuthorResponse(
        id=author_id,
        name="New Name",
        books=[BookSchema(title="Old Book")],
        birth_date=date(1990, 1, 1),
        country="New Country"
    )
    mock_service.update_author.return_value = expected_response

    response = test_client.put(
        f"/v1/authors-books/{author_id}",
        json={
            "name": "New Name",
            "country": "New Country"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["country"] == "New Country"

def test_update_author_not_found(client):
    test_client, mock_service = client
    author_id = uuid4()

    mock_service.update_author.side_effect = NotFoundError("Author", str(author_id))

    response = test_client.put(
        f"/v1/authors-books/{author_id}",
        json={
            "name": "New Name",
            "country": "New Country"
        }
    )
    assert response.status_code == 404

def test_delete_author_success(client):
    test_client, mock_service = client
    author_id = uuid4()

    mock_service.delete_author.return_value = None

    response = test_client.delete(f"/v1/authors-books/{author_id}")

    assert response.status_code == 204

def test_delete_author_not_found(client):
    test_client, mock_service = client
    author_id = uuid4()

    mock_service.delete_author.side_effect = NotFoundError("Author", str(author_id))

    response = test_client.delete(f"/v1/authors-books/{author_id}")

    assert response.status_code == 404
