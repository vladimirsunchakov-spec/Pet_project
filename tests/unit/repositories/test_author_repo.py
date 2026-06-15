import pytest
from dulwich import repo

from src.models.authors import AuthorModel
from src.models.books import BookModel
from src.repositories.author_repository import AuthorRepository
from sqlalchemy.orm import selectinload
from sqlalchemy import select

@pytest.mark.asyncio
async def test_create_author(db_session):
    repo = AuthorRepository(db_session)

    author = await repo.create(name="Test Author")

    assert author.id is not None
    assert author.name == "Test Author"
    assert author.is_deleted is False

@pytest.mark.asyncio
async def test_get_author_by_id(db_session):
    repo = AuthorRepository(db_session)

    created = await repo.create(name="Test Author")
    found = await repo.get(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.name == "Test Author"

@pytest.mark.asyncio
async def test_get_author_not_found(db_session):
    repo = AuthorRepository(db_session)

    found = await repo.get(9999)

    assert found is None

@pytest.mark.asyncio
async def test_get_all_authors(db_session):
    repo = AuthorRepository(db_session)

    await repo.create(name="Author 1")
    await repo.create(name="Author 2")
    await repo.create(name="Author 3")

    authors = await repo.get_all()

    assert len(authors) == 3
    assert authors[0].name == "Author 1"
    assert authors[1].name == "Author 2"
    assert authors[2].name == "Author 3"

@pytest.mark.asyncio
async def test_update_author(db_session):
    repo = AuthorRepository(db_session)

    author = await repo.create(name="Old Author")
    updated = await repo.update(author.id, name="New Name")

    assert updated.name is not None
    assert updated.name == "New Name"

@pytest.mark.asyncio
async def test_soft_delete_author(db_session):
    repo = AuthorRepository(db_session)

    author = await repo.create(name="Test Author")
    result = await repo.soft_delete(author.id)

    assert result is True

    deleted = await repo.get(author.id)
    assert deleted is None

@pytest.mark.asyncio
async def test_get_with_books(db_session):
    repo = AuthorRepository(db_session)

    author = await repo.create(name="Test Author")

    book1 = BookModel(title="Book 1")
    book2 = BookModel(title="Book 2")
    db_session.add(book1)
    db_session.add(book2)
    await db_session.flush()

    author_with_books = await repo.get_with_books(author.id)

    author_with_books.books.append(book1)
    author_with_books.books.append(book2)
    await db_session.flush()

    found = await repo.get_with_books(author.id)

    assert found is not None
    assert found.id == author.id
    assert len(found.books) == 2
    assert found.books[0].title == "Book 1"
    assert found.books[1].title == "Book 2"
