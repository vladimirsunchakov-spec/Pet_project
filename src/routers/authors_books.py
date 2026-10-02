from fastapi import APIRouter, Depends, status, Query, HTTPException
from uuid import UUID
from src.services.authors_books import AuthorsBooksService
from src.schemas.authors import AuthorCreate, AuthorUpdate, AuthorResponse
from src.dependencies import get_authors_books_service
from typing import List
from src.exceptions import NotFoundError

router = APIRouter(prefix="/v1/authors-books", tags=["Authors & Books"])

@router.post("/", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED, summary="Создать автора", description="Создает автора с bio через saga")
async def create_author(
    data: AuthorCreate,
    service: AuthorsBooksService = Depends(get_authors_books_service)):

    return await service.create_author(data)

@router.get("/{author_id}", response_model=AuthorResponse, summary="Получить автора", description="Получает автора с bio")
async def get_author(
    author_id: UUID,
    service: AuthorsBooksService = Depends(get_authors_books_service)):
    try:
        return await service.get_author(author_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/authors", response_model=List[AuthorResponse], summary="Получить авторов", description="Получает авторов с пагинацией")
async def get_authors(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=0, le=1000, description="Количество записей на странице"),
    service: AuthorsBooksService = Depends(get_authors_books_service)):

    return await service.get_authors(skip=skip, limit=limit)

@router.put("/{author_id}", response_model=AuthorResponse, summary="Обновить автора", description="Обновляет автора")
async def update_author(
    author_id: UUID,
    data: AuthorUpdate,
    service: AuthorsBooksService = Depends(get_authors_books_service)):
    try:
        return await service.update_author(author_id, data)
    except NotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить автора", description="Мягкое удаление автора через Saga")
async def delete_author(
    author_id: UUID,
    service: AuthorsBooksService = Depends(get_authors_books_service)):
    try:
        await service.delete_author(author_id)
    except NotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
