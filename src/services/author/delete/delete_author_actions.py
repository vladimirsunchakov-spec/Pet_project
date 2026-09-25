from uuid import UUID
from typing import Optional
from src.repositories.author_repository import AuthorRepository
from src.clients.bio_client import BioServiceClient
from src.exceptions import (ExternalServiceError, ExternalServiceUnavailableError, NotFoundError)
import logging

logger = logging.getLogger(__name__)

class DeleteAuthorActions:
    def __init__(
        self,
        author_repo: AuthorRepository,
        bio_client: BioServiceClient,
        author_id: UUID
    ):
        self.author_id = author_id
        self.author_repo = author_repo
        self.bio_client = bio_client
        self._original_bio_status = "active"

    async def delete_bio(self, idempotency_key: Optional[str] = None) -> bool:
        logger.info(f"Soft deleting bio for author {self.author_id}")

        try:
            bio_data = await self.bio_client.get_bio_by_author_id(self.author_id)
        except NotFoundError:
            logger.info(f"No bio to delete for author {self.author_id}")
            return True

        except ExternalServiceUnavailableError as e:
            logger.error(f"Bio service unavailable: {e}")
            raise

        except ExternalServiceError as e:
            logger.error(f"Failed to get bio: {e}")
            raise

        self._original_bio_status = bio_data.status
        logger.info(f"Original bio status: {self._original_bio_status}")

        await self.bio_client.update_bio_status(self.author_id, status="deleted", idempotency_key=idempotency_key)
        logger.info(f"Bio status updated to 'deleted' for author {self.author_id}")
        return True

    async def delete_author(self) -> bool:
        logger.info(f"Soft deleting author {self.author_id}")

        deleted = await self.author_repo.soft_delete(self.author_id)
        if not deleted:
            logger.warning(f"Author {self.author_id} not found for soft delete")
            raise NotFoundError("Author", str(self.author_id))

        logger.info(f"Author {self.author_id} soft deleted")
        return True

    async def restore_bio(self):
        logger.info(f"Compensating: restoring bio for author {self.author_id}")
        await self.bio_client.update_bio_status(self.author_id, status=self._original_bio_status)
        logger.info(f"Bio status restored to '{self._original_bio_status}' " f"for author {self.author_id}")

    async def restore_author(self):
        logger.info(f"Compensating: restoring author {self.author_id}")
        await self.author_repo.restore(self.author_id)
        logger.info(f"Author {self.author_id} restored")

