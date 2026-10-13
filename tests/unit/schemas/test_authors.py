import pytest
from datetime import date
from uuid import uuid4
import src.models
from src.schemas.authors import AuthorCreate, AuthorUpdate, AuthorResponse, BookSchema
from src.exceptions import ValidationError
from src.models.authors import AuthorModel

class TestBookSchema:
    def test_vali_book(self):
        book = BookSchema(title="War and Peace")
        assert book.title == "War and Peace"

    def test_to_model(self):
        book = BookSchema(title="1984")
        model = book.to_model()
        assert model.title == "1984"

class TestAuthorCreate:
    def test_valid_author_create(self):
        data = AuthorCreate(
            name="Leo Tolstoy",
            books=[BookSchema(title = "War and Peace")],
            birth_date=date(1901, 1, 1),
            country="Russia"
        )
        assert data.name == "Leo Tolstoy"
        assert len(data.books) == 1
        assert data.birth_date == date(1901, 1, 1)
        assert data.country == "Russia"

    def test_name_empty_raises_error(self):
        with pytest.raises(ValidationError, match="Author name cannot be empty"):
            AuthorCreate(
                name=" ",
                books=[BookSchema(title = "War and Peace")]
            )

    def test_books_empty_raises_error(self):
        with pytest.raises(ValueError):
            AuthorCreate(
                name="Leo Tolstoy",
                books=[]
            )

    def test_birth_date_future_raises_error(self):
        future_date = date(2099, 1, 1)
        with pytest.raises(ValidationError):
            AuthorCreate(
                name="Leo Tolstoy",
                books=[BookSchema(title = "War and Peace")],
                birth_date=future_date
            )

    def test_birth_date_too_old_raises_error(self):
        old_date = date(1800, 1,1)
        with pytest.raises(ValidationError):
            AuthorCreate(
                name="Leo Tolstoy",
                books=[BookSchema(title = "War and Peace")],
                birth_date=old_date
            )

    def test_to_model(self):
        data = AuthorCreate(
            name="Leo Tolstoy",
            books=[BookSchema(title = "War and Peace")],
            birth_date=date(1901, 1, 1),
            country="Russia"
        )
        model = data.to_model()
        assert model.name == "Leo Tolstoy"
        assert len(model.books) == 1
        assert model.books[0].title == "War and Peace"
        assert model.birth_date == date(1901, 1, 1)
        assert model.country == "Russia"

class TestAuthorUpdate:
    def test_valid_update(self):
        data = AuthorUpdate(
            name="Update name",
            country="Update Country",
        )
        assert data.name == "Update name"
        assert data.country == "Update Country"

    def test_update_with_none(self):
        data = AuthorUpdate()
        assert data.name is None
        assert data.birth_date is None
        assert data.country is None

    def test_update_model(self):
        author = AuthorModel(name="Old Name", country="Old Country")
        data = AuthorUpdate(name="New Name", country="New Country")
        data.update_model(author)

        assert author.name == "New Name"
        assert author.country == "New Country"

class TestAuthorResponse:
    def test_valid_response(self):
        author_id = uuid4()
        response = AuthorResponse(
            id=author_id,
            name="Leo Tolstoy",
            books=[BookSchema(title = "War and Peace")],
            birth_date=date(1828, 9, 9),
            country="Russia"
        )
        assert response.id == author_id
        assert response.name == "Leo Tolstoy"
        assert len(response.books) == 1
        assert response.books[0].title == "War and Peace"

    def test_response_with_bio_fields(self):
        author_id = uuid4()
        response = AuthorResponse(
            id=author_id,
            name="Leo Tolstoy",
            books=[BookSchema(title = "War and Peace")],
            birth_date=date(1828, 9, 9),
            country="Russia",
            rating=4.5,
            awards_count=10
        )
        assert response.rating == 4.5
        assert response.awards_count == 10









