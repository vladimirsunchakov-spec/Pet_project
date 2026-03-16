from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.services.authors_books import AuthorsBooksService
from src.schemas.books import BookCreate, BookUpdate, BookResponse
from src.schemas.authors import AuthorCreate, AuthorUpdate, AuthorResponse
from src.db import get_session
from src.schemas.base import StatusResponse
from src.exceptions import NotFoundError

router = APIRouter(prefix="/v1/authors-books", tags=["Authors & Books"])

@router.post("/", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author(
    data: AuthorCreate,
    db: AsyncSession = Depends(get_session)):
    author = await AuthorsBooksService.create_author(db, data)
    await db.commit()
    await db.refresh(author)
    return AuthorResponse.model_validate(author)

@router.get("/{author_id}", response_model=AuthorResponse)
async def get_author(
    author_id: UUID,
    db: AsyncSession = Depends(get_session)):
    author = await AuthorsBooksService.get_author(db, author_id)
    if not author:
        raise NotFoundError("Author not found")
    return AuthorResponse.model_validate(author)

@router.put("/{author_id}", response_model=AuthorResponse)
async def update_author(
    author_id: UUID,
    data: AuthorUpdate,
    db: AsyncSession = Depends(get_session)):
    author = await AuthorsBooksService.update_author(db, author_id, data)
    await db.commit()
    await db.refresh(author)
    return AuthorResponse.model_validate(author)

@router.delete("/{author_id}", response_model=StatusResponse, status_code=status.HTTP_200_OK)
async def delete_author(
    author_id: UUID,
    db: AsyncSession = Depends(get_session)):
    result = await AuthorsBooksService.delete_author(db, author_id)
    await db.commit()
    return result

@router.post("/{author_id}/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def add_book_to_author(
    author_id: UUID,
    data: BookCreate,
    db: AsyncSession = Depends(get_session)):
    book = await AuthorsBooksService.add_book_to_author(db, author_id, data)
    await db.commit()
    await db.refresh(book)
    return BookResponse.model_validate(book)

@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_session)):
    book = await AuthorsBooksService.get_book(db, book_id)
    if not book:
        raise NotFoundError("Book not found")
    return BookResponse.model_validate(book)

@router.put("/books/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: UUID,
    data: BookUpdate,
    db: AsyncSession = Depends(get_session)):
    book = await AuthorsBooksService.update_book(db, book_id, data)
    await db.commit()
    await db.refresh(book)
    return BookResponse.model_validate(book)

@router.delete("/books/{book_id}", response_model=StatusResponse, status_code=status.HTTP_200_OK)
async def delete_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_session)):
    result = await AuthorsBooksService.delete_book(db, book_id)
    await db.commit()
    return result