from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.author_repository import AuthorRepository
from src.clients.bio_client import BioServiceClient, BioServiceError
import logging

from tests.conftest import db_session

logger = logging.getLogger(__name__)

class DeleteAuthorActions:
    def __init__(self, db_session: AsyncSession, author_id: UUID):
        self.db_session = db_session
        self.author_id = author_id
        self.author_repo = AuthorRepository(db_session)
        self.bio_client = BioServiceClient()

    async def delete_bio(self) -> bool:
        logger.info(f"Deleting bio for author {self.author_id}")

        try:
            bio = await self.bio_client.get_bio_by_author_id(self.author_id)
            if not bio:
                logger.info(f"No bio to delete for author {self.author_id}")
                return True

            logger.info(f"Bio deleted for author {self.author_id}")
            return True

        except BioServiceError as e:
            logger.error(f"Failed to delete bio: {e}")
            raise

    async def delete_author(self) -> bool:
        logger.info(f"Deleting author {self.author_id}")

        deleted = await self.author_repo.soft_delete(self.author_id)
        if not deleted:
            raise Exception(f"Author {self.author_id} not found")

        logger.info(f"Author {self.author_id} deleted")
        return True

    async def restore_bio(self):
        logger.info(f"Restoring bio for author {self.author_id}")
        pass

    async def restore_author(self):
        logger.info(f"Restoring author {self.author_id}")
        pass
