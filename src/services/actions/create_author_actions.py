from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.author_repository import AuthorRepository
from src.clients.bio_client import BioServiceClient, BioServiceError
from src.schemas.authors import AuthorCreate
from workers.bio_worker import bio_worker
import logging

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
            return {
                "bio_created": False,
                "scheduled_in_worker": True,
                "message": "Bio creation scheduled in background"
            }

    async def compensate_author(self, author_id: UUID):
        logger.info(f"Compensating author {author_id}")
        await self.author_repo.soft_delete(author_id)

    async def compensate_bio(self, author_id: UUID):
        logger.info(f"Compensating Bio for author {author_id}")
        pass
