from uuid import UUID
from src.repositories.author_repository import AuthorRepository
from src.clients.bio_client import BioServiceClient
from src.exceptions import (
    ExternalServiceError,
    ExternalServiceUnavailableError,
    NotFoundError,
)
import logging

logger = logging.getLogger(__name__)


class DeleteAuthorActions:
    def __init__(
        self,
        author_repo: AuthorRepository,
        bio_client: BioServiceClient,
        author_id: UUID,
    ):
        self.author_id = author_id
        self.author_repo = author_repo
        self.bio_client = bio_client

    async def delete_bio(self) -> bool:
        try:
            await self.bio_client.get_bio_by_author_id(self.author_id)
        except NotFoundError:
            return True
        except (ExternalServiceUnavailableError, ExternalServiceError):
            raise

        logger.warning(
            "Bio status update skipped for author %s: not supported by bio client",
            self.author_id,
        )
        return True

    async def delete_author(self) -> bool:
        deleted = await self.author_repo.soft_delete(self.author_id)
        if not deleted:
            raise NotFoundError("Author", str(self.author_id))
        return True

    async def restore_bio(self) -> None:
        logger.warning(
            "Bio restore skipped for author %s: status update is not supported by bio client",
            self.author_id,
        )

    async def restore_author(self) -> None:
        await self.author_repo.restore(self.author_id)
