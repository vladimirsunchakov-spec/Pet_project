from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from services.saga.base_saga import BaseSaga
from src.repositories.author_repository import AuthorRepository
from src.clients.bio_client import BioServiceClient, BioServiceError
import logging

logger = logging.getLogger(__name__)

class DeleteAuthorSaga(BaseSaga):
    def __init__(self, db_session: AsyncSession, author_id: UUID, saga_id: Optional[str] = None):
        super().__init__(saga_id)
        self.db_session = db_session
        self.author_id = author_id
        self.author_repo = AuthorRepository(db_session)
        self.bio_client = BioServiceClient()

        self.state.context["author_id"] = str(author_id)

        self._build_saga()

    def _build_saga(self):
        self.add_step(
            name="delete_bio",
            action=self._delete_bio,
            compensation=self._restore_bio
        )
        self.add_step(
            name="delete_author",
            action=self._delete_author,
            compensation=self._restore_author
        )

    async def _delete_bio(self) -> bool:
        logger.info(f"Saga {self.saga_id}: Deleting bio for author {self.author_id}")

        try:
            bio = await self.bio_client.get_bio_by_author_id(self.author_id)
            if not bio:
                logger.info(f"Saga {self.saga_id}: No bio to delete for author {self.author_id}")
                return True

            logger.info(f"Saga {self.saga_id}: Bio deleted for author {self.author_id}")
            return True

        except BioServiceError as e:
            logger.error(f"Saga {self.saga_id}: Failed to delete bio: {e}")
            raise

    async def _restore_bio(self):
        logger.info(f"Saga {self.saga_id}: Restoring bio for author {self.author_id}")
        pass

    async def _delete_author(self):
        logger.info(f"Saga {self.saga_id}: Deleting author {self.author_id}")

        deleted = await self.author_repo.soft_delete(self.author_id)

        if not deleted:
            raise Exception(f"Author {self.author_id} not found")

        logger.info(f"Saga {self.saga_id}: Author {self.author_id} deleted")
        return True

    async def _restore_author(self):
        logger.info(f"Saga {self.saga_id}: Restoring author {self.author_id}")
        pass


