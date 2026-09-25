from uuid import UUID
from typing import Optional
from src.repositories.task_repository import TaskRepository
from src.repositories.author_repository import AuthorRepository
from src.clients.bio_client import BioServiceClient
from src.exceptions import (ExternalServiceUnavailableError, ExternalServiceError)
from src.schemas.authors import AuthorCreate
import logging

logger = logging.getLogger(__name__)

class CreateAuthorActions:
    def __init__(self, author_repo: AuthorRepository, bio_client: BioServiceClient, task_repo: TaskRepository, author_data: dict):
        self.author_data = author_data
        self.author_repo = author_repo
        self.bio_client = bio_client
        self.task_repo = task_repo

    async def create_author(self) -> dict:
        logger.info("Creating author")
        author_create = AuthorCreate(**self.author_data)
        author = author_create.to_model()
        created_author = await self.author_repo.create_author(author)
        return {"author_id": str(created_author.id)}

    async def create_bio(self, author_id: UUID, idempotency_key: Optional[str] = None) -> dict:
        logger.info(f"Creating Bio for author {author_id}")
        try:
            bio_data = await self.bio_client.create_bio(author_id=author_id, idempotency_key=idempotency_key)
            logger.info(f"Bio created successfully for author {author_id}")
            return {"bio_created": True, "bio_data": bio_data}

        except ExternalServiceUnavailableError as e:
            logger.warning(
                f"Bio service unavailable for after all retries,"
                f"scheduling in worker: {e}"
            )
            await self.task_repo.create_task(
                task_type="create_bio",
                payload={
                    "author_id": str(author_id),
                    "rating": self.author_data.get("rating", 0.0),
                    "awards_count": self.author_data.get("awards_count", 0),
                },
            )
            return {
                "bio_created": False,
                "deferred": True,
                "scheduled_in_worker": True,
                "message": "Bio creation scheduled in background",
            }
        except ExternalServiceError as e:
            logger.error(f"Bio creation failed with  client error: {e}")
            raise

    async def compensate_author(self, author_id: UUID):
        logger.info(f"Compensating author {author_id}")
        await self.author_repo.soft_delete(author_id)

    async def compensate_bio(self, author_id: UUID):
        logger.info(f"Compensating Bio for author {author_id}")
        await self.bio_client.update_bio_status(author_id, status="deleted")
