from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.author_repository import AuthorRepository
from src.clients.bio_client import BioServiceClient, BioServiceError
import logging

logger = logging.getLogger(__name__)

class DeleteAuthorActions:
    def __init__(self, db_session: AsyncSession, author_id: UUID):
        self.db_session = db_session
        self.author_id = author_id
        self.author_repo = AuthorRepository(db_session)
        self.bio_client = BioServiceClient()
        self._original_bio_status = "active"

    async def delete_bio(self) -> bool:
        logger.info(f"Soft deleting bio for author {self.author_id}")

        try:
            bio_data = await self.bio_client.get_bio_by_author_id(self.author_id)
            if not bio_data:
                logger.info(f"No bio to delete for author {self.author_id}")
                return True

            self._original_bio_status = bio_data.get("status", "active")
            logger.info(f"Original bio status: {self._original_bio_status}")

            await self.bio_client.update_bio_status(self.author_id, status="deleted")

            logger.info(f"Bio status update to 'deleted' for author {self.author_id}")
            return True

        except BioServiceError as e:
            logger.error(f"Failed to update bio status: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in delete_bio: {e}")
            raise

    async def delete_author(self) -> bool:
        logger.info(f"Soft deleting author {self.author_id}")

        deleted = await self.author_repo.soft_delete(self.author_id)
        if not deleted:
            logger.warning(f"Author {self.author_id} not found for soft delete")
            raise Exception(f"Author {self.author_id} not found")

        logger.info(f"Author {self.author_id} deleted")
        return True

    async def restore_bio(self):
        logger.info(f"Compensating: restoring bio for author {self.author_id}")
        try:
            await self.bio_client.update_bio_status(self.author_id, status=self._original_bio_status)
            logger.info(f"Bio status restored to '{self._original_bio_status}' " f"for author {self.author_id}")
        except Exception as e:
            logger.error(f"Failed to restore bio: {e}")
            raise

    async def restore_author(self):
        logger.info(f"Compensating: restoring author {self.author_id}")
        try:
            await self.author_repo.restore(self.author_id)
            logger.info(f"Author {self.author_id} restored")
        except Exception as e:
            logger.error(f"Failed to restore author: {e}")
            raise

