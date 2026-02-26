from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.services.books import BookService
from src.schemas.books import BookCreate, BookUpdate, BookResponse
from src.db import get_session

router = APIRouter(prefix="/books", tags=["Books"])

@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    data: BookCreate,
    db: AsyncSession = Depends(get_session)):
    """
    Создание новой книги.
    :param data: данные книги (title)
    :return: BookResponse: созданная книга
    """
    return await BookService.create(db, data)

@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_session)):
    """
    Получение книги по ID.
    :param book_id: UUID книги
    :return: BookResponse: книга
    """
    return await BookService.get_by_id(db, book_id)

@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: UUID,
    data: BookUpdate,
    db: AsyncSession = Depends(get_session)):
    """
    Обновление книги.
    :param book_id: UUID книги
    :param data: новые данные (title)
    :return: BookResponse: обновлённая книга
    """
    return await BookService.update(db, book_id, data)

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_session)):
    """
    Удаление книги по ID.
    :param book_id: UUID книги
    :return: 204 No Content при успешном удалении
    """
    await BookService.delete(db, book_id)
    return None
