from uuid import UUID
from src.repositories.task_repository import TaskRepository
from src.repositories.author_repository import AuthorRepository
from src.clients.bio_client import BioServiceClient
from src.exceptions import ExternalServiceUnavailableError, ExternalServiceError
from src.schemas.authors import AuthorCreate
import logging

logger = logging.getLogger(__name__)


class CreateAuthorActions:
    def __init__(
        self,
        author_repo: AuthorRepository,
        bio_client: BioServiceClient,
        task_repo: TaskRepository,
        author_data: AuthorCreate,
    ):
        self.author_data = author_data
        self.author_repo = author_repo
        self.bio_client = bio_client
        self.task_repo = task_repo

    async def create_author(self) -> dict:
        author = self.author_data.to_model()
        created_author = await self.author_repo.create_author(author)
        return {"author_id": str(created_author.id)}

    async def create_bio(self, author_id: UUID, idempotency_key: str) -> dict:
        try:
            bio_data = await self.bio_client.create_bio(
                author_id=author_id,
                idempotency_key=idempotency_key,
            )
            return {"bio_created": True, "bio_data": bio_data}

        except ExternalServiceUnavailableError as e:
            logger.warning(
                "Bio service unavailable, scheduling create_bio task for author %s: %s",
                author_id,
                e,
            )
            await self.task_repo.create_task(
                task_type="create_bio",
                payload={
                    "author_id": str(author_id),
                    "rating": 0.0,
                    "awards_count": 0,
                },
            )
            return {
                "bio_created": False,
                "deferred": True,
                "scheduled_in_worker": True,
                "message": "Bio creation scheduled in background",
            }
        except ExternalServiceError:
            raise

    async def compensate_author(self, author_id: UUID) -> None:
        await self.author_repo.soft_delete(author_id)

    async def compensate_bio(self, author_id: UUID) -> None:
        logger.warning(
            "Bio compensation skipped for author %s: status update is not supported by bio client",
            author_id,
        )
