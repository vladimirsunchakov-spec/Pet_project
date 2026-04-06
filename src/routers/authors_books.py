from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.services.authors_books import AuthorsBooksService
from src.schemas.authors import AuthorCreate, AuthorUpdate, AuthorResponse
from src.db import get_session

router = APIRouter(prefix="/v1/authors-books", tags=["Authors & Books"])

@router.post("/", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author(
    data: AuthorCreate,
    db: AsyncSession = Depends(get_session)):
    service = AuthorsBooksService(db=db)
    author = await service.create_author(data=data)
    return AuthorResponse.model_validate(author)

@router.get("/{author_id}", response_model=AuthorResponse)
async def get_author(
    author_id: UUID,
    db: AsyncSession = Depends(get_session)):
    service = AuthorsBooksService(db=db)
    author = await service.get_author(author_id=author_id)
    return AuthorResponse.model_validate(author)

@router.put("/{author_id}", response_model=AuthorResponse)
async def update_author(
    author_id: UUID,
    data: AuthorUpdate,
    db: AsyncSession = Depends(get_session)):
    service = AuthorsBooksService(db=db)
    author = await service.update_author(author_id=author_id, data=data)
    return AuthorResponse.model_validate(author)

@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_author(
    author_id: UUID,
    db: AsyncSession = Depends(get_session)):
    service = AuthorsBooksService(db=db)
    await service.delete_author(author_id=author_id)
