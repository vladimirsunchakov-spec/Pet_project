from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.clients.bio_client import BioServiceClient
from src.repositories.author_repository import AuthorRepository
from src.schemas.saga import SagaState
from src.services.author.shared.base_saga import BaseSaga
from src.services.author.delete.delete_author_actions import DeleteAuthorActions
import logging

logger = logging.getLogger(__name__)

class DeleteAuthorSaga(BaseSaga):
    def __init__(
        self,
        db_session: AsyncSession,
        author_id: UUID,
        author_repo: AuthorRepository,
        bio_client: BioServiceClient,
        saga_id: Optional[str] = None,
        restore_from_state: Optional[SagaState] = None,
    ):
        super().__init__(saga_id=saga_id, db_session=db_session, restore_from_state=restore_from_state)
        self.actions = DeleteAuthorActions(
            author_repo=author_repo,
            bio_client=bio_client,
            author_id=author_id,
        )
        self.state.context["author_id"] = str(author_id)
        self._build_saga()

    def _build_saga(self):
        self.add_step(
            name="delete_bio",
            action=self._step_delete_bio,
            compensation=self.actions.restore_bio
        )
        self.add_step(
            name="delete_author",
            action=self.actions.delete_author,
            compensation=self.actions.restore_author
        )

    async def _step_delete_bio(self) -> dict:
        idempotency_key = self.state.context.get("idempotency_key")
        await self.actions.delete_bio(idempotency_key=idempotency_key)
        logger.info(
            f"Saga {self.saga_id}: Bio marked as deleted "
            f"for author {self.state.context['author_id']}"
        )
        return {"bio_deleted": True}

