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
    params = {
        "db": db,
        "data": data,
        "request": request.state.request_id
    }
    author = await AuthorsBooksService.create_author(**params)
    await db.refresh(author)
    return AuthorResponse.model_validate(author)

@router.get("/{author_id}", response_model=AuthorResponse)
async def get_author(
    request: Request,
    author_id: UUID,
    db: AsyncSession = Depends(get_session)):
    params = {
        "db": db,
        "author_id": author_id,
        "request": request.state.request_id
    }
    author = await AuthorsBooksService.get_author(**params)
    if not author:
        raise NotFoundError("Author not found")
    return AuthorResponse.model_validate(author)

@router.put("/{author_id}", response_model=AuthorResponse)
async def update_author(
    request: Request,
    author_id: UUID,
    data: AuthorUpdate,
    db: AsyncSession = Depends(get_session)):
    params = {
        "db": db,
        "author_id": author_id,
        "data": data,
        "request": request.state.request_id
    }
    author = await AuthorsBooksService.update_author(**params)
    await db.refresh(author)
    return AuthorResponse.model_validate(author)

@router.delete("/{author_id}", response_model=StatusResponse, status_code=status.HTTP_200_OK)
async def delete_author(
    request: Request,
    author_id: UUID,
    db: AsyncSession = Depends(get_session)):
    params = {
        "db": db,
        "author_id": author_id,
        "request": request.state.request_id
    }
    result = await AuthorsBooksService.delete_author(**params)
    return result

@router.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
        request: Request,
        data: BookCreate,
        db: AsyncSession = Depends(get_session)
):
        params = {
            "db": db,
            "data": data,
            "request": request.state.request_id
        }
        book = await AuthorsBooksService.create_book(**params)
        await db.refresh(book)
        return BookResponse.model_validate(book)

@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(
    request: Request,
    book_id: UUID,
    db: AsyncSession = Depends(get_session)):
    params = {
        "db": db,
        "book_id": book_id,
        "request": request.state.request_id
    }
    book = await AuthorsBooksService.get_book(**params)
    if not book:
        raise NotFoundError("Book not found")
    return BookResponse.model_validate(book)

@router.put("/books/{book_id}", response_model=BookResponse)
async def update_book(
    request: Request,
    book_id: UUID,
    data: BookUpdate,
    db: AsyncSession = Depends(get_session)):
    params = {
        "db": db,
        "book_id": book_id,
        "data": data,
        "request": request.state.request_id
    }
    book = await AuthorsBooksService.update_book(**params)
    await db.refresh(book)
    return BookResponse.model_validate(book)

@router.delete("/books/{book_id}", response_model=StatusResponse, status_code=status.HTTP_200_OK)
async def delete_book(
    request: Request,
    book_id: UUID,
    db: AsyncSession = Depends(get_session)):
    params = {
        "db": db,
        "book_id": book_id,
        "request": request.state.request_id
    }
    result = await AuthorsBooksService.delete_book(**params)
    return result