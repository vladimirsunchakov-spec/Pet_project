from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.services.authors_books import AuthorsBooksService
from src.schemas.books import BookCreate, BookUpdate, BookResponse
from src.schemas.authors import AuthorCreate, AuthorUpdate, AuthorResponse
from src.db import get_session
from src.schemas.base import StatusResponse

router = APIRouter(prefix="/v1/authors-books", tags=["Authors & Books"])

@router.post("/authors", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author(
    data: AuthorCreate,
    db: AsyncSession = Depends(get_session)):

    return await AuthorsBooksService.create_author(db, data)

@router.get("/authors/{author_id}", response_model=AuthorResponse)
async def get_author(
    author_id: UUID,
    db: AsyncSession = Depends(get_session)):

    return await AuthorsBooksService.get_author(db, author_id)

@router.put("/authors/{author_id}", response_model=AuthorResponse)
async def update_author(
    author_id: UUID,
    data: AuthorUpdate,
    db: AsyncSession = Depends(get_session)):

    return await AuthorsBooksService.update_author(db, author_id, data)

@router.delete("/authors/{author_id}", response_model=StatusResponse, status_code=status.HTTP_204_NO_CONTENT)
async def delete_author(
    author_id: UUID,
    db: AsyncSession = Depends(get_session)):

    await AuthorsBooksService.delete_author(db, author_id)
    return StatusResponse(status="deleted")

@router.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(data: BookCreate, db: AsyncSession = Depends(get_session)):
    return await AuthorsBooksService.create_book(db, data)

@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: UUID, db: AsyncSession = Depends(get_session)):
    return await AuthorsBooksService.get_book(db, book_id)

@router.put("/books/{book_id}", response_model=BookResponse)
async def update_book(book_id: UUID, data: BookUpdate, db: AsyncSession = Depends(get_session)):
    return await AuthorsBooksService.update_book(db, book_id, data)

@router.delete("/books/{book_id}", response_model=StatusResponse, status_code=status.HTTP_200_OK)
async def delete_book(book_id: UUID, db: AsyncSession = Depends(get_session)):
    await AuthorsBooksService.delete_book(db, book_id)
    return StatusResponse(status="deleted")