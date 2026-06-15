from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from service2.src2.services.bio_service import BioService
from service2.src2.schemas.author_bio import BioCreate, BioUpdate, BioResponse
from service2.src2.db import get_session
from service2.src2.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/bio", tags=["Bio"])

@router.post("/", response_model=BioResponse, status_code=status.HTTP_201_CREATED)
async def create_bio(data: BioCreate, db: AsyncSession = Depends(get_session)):
    service = BioService(db)
    return await service.create_bio(data)

@router.get("/{author_id}", response_model=BioResponse)
async def get_bio_by_author_id(author_id: UUID, db: AsyncSession = Depends(get_session)):
    service = BioService(db)
    return await service.get_bio_by_author_id(author_id)

@router.get("/", response_model=List[BioResponse])
async def get_all_bios(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_session)):
    service = BioService(db)
    return await service.get_all_bios(skip, limit)

@router.put("/{author_id}", response_model=BioResponse)
async def update_bio_by_author_id(author_id: UUID, data: BioUpdate, db: AsyncSession = Depends(get_session)):
    service = BioService(db)
    return await service.update_bio_by_author_id(author_id, data)

@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bio_by_author_id(author_id: UUID, db: AsyncSession = Depends(get_session)):
    service = BioService(db)
    await service.delete_bio_by_author_id(author_id)
    return None
