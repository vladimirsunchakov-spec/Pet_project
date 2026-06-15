from uuid import UUID
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from service2.src2.repositories.bio_repository import BioRepository
from service2.src2.schemas.author_bio import BioCreate, BioUpdate, BioResponse
from service2.src2.exceptions import NotFoundError, ValidationError
from service2.src2.core.logger import get_request_id
from service2.src2.services.base import BaseService

class BioService(BaseService):
    def __init__(self, db: AsyncSession):
        self.db = db
        self.request_id = get_request_id()
        self.bio_repo = BioRepository(db)

    async def create_bio(self, data: BioCreate) -> BioResponse:
        self._log_info("Creating bio for author", author_id=str(data.author_id), request_id=self.request_id)
        existing = await self.bio_repo.get_by_author_id(data.author_id)
        if existing:
            self._log_warning("Bio already exists for author", author_id=str(data.author_id), request_id=self.request_id)
            raise ValidationError(f"Bio for author {data.author_id} already exists")

        bio = await self.bio_repo.create(
            author_id=data.author_id,
            rating=data.rating,
            awards_count=data.awards_count,
            biography=data.biography,
        )
        self._log_info("Bio created", bio_id=str(bio.id), author_id=str(data.author_id), request_id=self.request_id)
        return BioResponse.model_validate(bio)

    async def get_bio_by_author_id(self, author_id: UUID) -> BioResponse:
        self._log_info("Fetching bio by author_id", author_id=str(author_id), request_id=self.request_id)
        bio = await self.bio_repo.get_by_author_id(author_id)
        if not bio:
            self._log_warning("Bio not found for author", author_id=str(author_id), request_id=self.request_id)
            raise NotFoundError("Bio", f"author_id={author_id}")
        return BioResponse.model_validate(bio)

    async def get_all_bios(self, skip: int = 0, limit: int = 100) -> List[BioResponse]:
        self._log_info("Fetching all bio", skip=skip, limit=limit, request_id=self.request_id)
        bios = await self.bio_repo.get_all_with_pagination(skip, limit)

        self._log_info("Bios fetched", count=len(bios), request_id=self.request_id)
        return [BioResponse.model_validate(bio) for bio in bios]

    async def update_bio_by_author_id(self, author_id: UUID, data: BioUpdate) -> BioResponse:
        self._log_info("Updating bio for author", author_id=str(author_id), request_id=self.request_id)
        bio = await self.bio_repo.get_by_author_id(author_id)
        if not bio:
            self._log_warning("Bio not found for author", author_id=author_id, request_id=self.request_id)
            raise NotFoundError("Bio", f"author_id={author_id}")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(bio, key, value)

        self._log_info("Bio updated", bio_id=str(bio.id), author_id=str(author_id), request_id=self.request_id)
        return BioResponse.model_validate(bio)

    async def delete_bio_by_author_id(self, author_id: UUID) -> None:
        self._log_info("Deleting bio for author", author_id=str(author_id), request_id=self.request_id)
        bio = await self.bio_repo.get_by_author_id(author_id)
        if not bio:
            self._log_warning("Bio not found for delete", author_id=str(author_id), request_id=self.request_id)
            raise NotFoundError("Bio", f"author_id={author_id}")

        await self.bio_repo.soft_delete(bio.id)

        self._log_info("Bio deleted", bio_id=str(bio.id), author_id=str(author_id), request_id=self.request_id)
