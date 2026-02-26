from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.services.authors import AuthorService
from src.schemas.authors import AuthorCreate, AuthorUpdate, AuthorResponse
from src.db import get_session

router = APIRouter(prefix="/authors", tags=["Authors"])

@router.post("/", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author(
    data: AuthorCreate,
    db: AsyncSession = Depends(get_session)):
    """
    Создание нового автора с вложенными книгами.
    :param data: данные автора (name, books)
    :return AuthorResponse: созданный автор со списком книг
    """
    return await AuthorService.create(db, data)

@router.get("/{author_id}", response_model=AuthorResponse)
async def get_author(
    author_id: UUID,
    db: AsyncSession = Depends(get_session)):
    """
    Получение автора по ID.
    :param author_id: UUID автора
    :return AuthorResponse: автор со списком книг
    """
    return await AuthorService.get_by_id(db, author_id)

@router.put("/{author_id}", response_model=AuthorResponse)
async def update_author(
    author_id: UUID,
    data: AuthorUpdate,
    db: AsyncSession = Depends(get_session)):
    """
    Полное обновление автора и его книг.
    :param author_id: UUID автора
    :param data:новые данные (name, books)
    :return:AuthorResponse: обновлённый автор
    """
    return await AuthorService.update(db, author_id, data)

@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_author(
    author_id: UUID,
    db: AsyncSession = Depends(get_session)):
    """
    Удаление автора по ID.
    :param author_id:UUID автора
    :return:204 No Content при успешном удалении
    """
    await AuthorService.delete(db, author_id)
    return None