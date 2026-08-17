from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from services.saga import BaseSaga
from src.repositories.author_repository import AuthorRepository
from src.clients.bio_client import BioServiceClient, BioServiceError
from src.schemas.authors import AuthorCreate
from src.worker import bio_worker
import logging
import asyncio

logger = logging.getLogger(__name__)

class CreateAuthorActions:
    def __init__(self, db_session: AsyncSession, author_data: dict):
        self.db_session = db_session
        self.author_data = author_data
        self.author_repo = AuthorRepository(db_session)
        self.bio_client = BioServiceClient()

    async def create_author(self) -> dict:
        logger.info("Creating author")
        author_create = AuthorCreate(**self.author_data)
        author = author_create.to_model()

        created_author = await self.author_repo.create_author(author)

        return {"author_id": str(created_author.id)}

    async def create_bio(self, author_id: UUID) -> dict:
        logger.info(f"Creating Bio for author {author_id}")
        try:
            bio_data = await self.bio_client.create_bio(author_id=author_id)
            logger.info(f"Bio created successfully")
            return {"bio_created": True, "bio_data": bio_data}
        except BioServiceError as e:
            logger.warning(f"All retries failed, scheduling bio creation in worker: {e}")
            await bio_worker.schedule_bio_creation(author_id)

            bio_created = await self._waiy_fro_bio_completion(author_id)

            if bio_created:
                return {"bio_created": True, "via_worker": True}
            else:
                raise Exception(f"Bio not created for author {author_id} after worker processing")

    async def _wait_for_bio_completion(self, author_id: UUID) -> bool:
        max_checks = 10
        check_interval = 1

        for check in range(1, max_checks + 1):
            await asyncio.sleep(check_interval)
            try:
                bio_data = await self.bio_client.get_bio_by_author_id(author_id)
                if bio_data:
                    return True
            except Exception:
                continue

        return False

    async def compensate_author(self, author_id: UUID):
        logger.info(f"Compensatinf author {author_id}")
        await self.author_repo.soft_delete(author_id)

    async def compensate_bio(self, author_id: UUID):
        logger.info(f"Compensating Bio for author {author_id}")
        pass
