from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.services.authors_books import AuthorsBooksService
from src.schemas.authors import AuthorCreate, AuthorUpdate, AuthorResponse
from src.db import get_session
from typing import List

router = APIRouter(prefix="/v1/authors-books", tags=["Authors & Books"])

@router.post("/", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author(
    data: AuthorCreate,
    db: AsyncSession = Depends(get_session)):

    return await AuthorsBooksService(db=db).create_author(data=data)

@router.get("/{author_id}", response_model=AuthorResponse)
async def get_author(
    author_id: UUID,
    db: AsyncSession = Depends(get_session)):

    return await AuthorsBooksService(db=db).get_author(author_id=author_id)

@router.get("/authors", response_model=List[AuthorResponse])
async def get_authors(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=0, le=1000, description="Количество записей на странице"),
    db: AsyncSession = Depends(get_session)):

    return await AuthorsBooksService(db=db).get_authors(skip=skip, limit=limit)

@router.put("/{author_id}", response_model=AuthorResponse)
async def update_author(
    author_id: UUID,
    data: AuthorUpdate,
    db: AsyncSession = Depends(get_session)):

    return await AuthorsBooksService(db=db).update_author(author_id=author_id, data=data)

@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_author(
    author_id: UUID,
    db: AsyncSession = Depends(get_session)):

    await AuthorsBooksService(db=db).delete_author(author_id=author_id)
