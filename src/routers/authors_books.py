from fastapi import APIRouter, Depends, status, Request
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
    request: Request,
    data: AuthorCreate,
    db: AsyncSession = Depends(get_session)):
    author = await AuthorsBooksService.create_author(db=db, data=data, request_id=request.state.request_id)
    await db.refresh(author)
    return AuthorResponse.model_validate(author)

@router.get("/{author_id}", response_model=AuthorResponse)
async def get_author(
    request: Request,
    author_id: UUID,
    db: AsyncSession = Depends(get_session)):
    author = await AuthorsBooksService.get_author(db=db, author_id=author_id, request_id=request.state.request_id)
    if not author:
        raise NotFoundError("Author not found")
    return AuthorResponse.model_validate(author)

@router.put("/{author_id}", response_model=AuthorResponse)
async def update_author(
    request: Request,
    author_id: UUID,
    data: AuthorUpdate,
    db: AsyncSession = Depends(get_session)):
    author = await AuthorsBooksService.update_author(db=db, author_id=author_id, data=data, request_id=request.state.request_id)
    await db.refresh(author)
    return AuthorResponse.model_validate(author)

@router.delete("/{author_id}", response_model=StatusResponse, status_code=status.HTTP_200_OK)
async def delete_author(
    request: Request,
    author_id: UUID,
    db: AsyncSession = Depends(get_session)):
    result = await AuthorsBooksService.delete_author(db=db, author_id=author_id, request_id=request.state.request_id)
    return result

@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(
    request: Request,
    book_id: UUID,
    db: AsyncSession = Depends(get_session)):
    book = await AuthorsBooksService.get_book(db=db, book_id=book_id, request_id=request.state.request_id)
    if not book:
        raise NotFoundError("Book not found")
    return BookResponse.model_validate(book)

@router.put("/books/{book_id}", response_model=BookResponse)
async def update_book(
    request: Request,
    book_id: UUID,
    data: BookUpdate,
    db: AsyncSession = Depends(get_session)):
    book = await AuthorsBooksService.update_book(db=db, book_id=book_id, data=data, request_id=request.state.request_id)
    await db.refresh(book)
    return BookResponse.model_validate(book)

@router.delete("/books/{book_id}", response_model=StatusResponse, status_code=status.HTTP_200_OK)
async def delete_book(
    request: Request,
    book_id: UUID,
    db: AsyncSession = Depends(get_session)):
    result = await AuthorsBooksService.delete_book(db=db, book_id=book_id, request_id=request.state.request_id)
    return result