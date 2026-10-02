from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.clients.bio_client import BioServiceClient
from src.repositories.author_repository import AuthorRepository
from src.schemas.saga import SagaState
from src.services.saga.base_saga import BaseSaga
from src.services.actions.delete_author_actions import DeleteAuthorActions


class DeleteAuthorSaga(BaseSaga):
    def __init__(
        self,
        db_session: AsyncSession,
        author_id: UUID,
        bio_client: BioServiceClient,
        saga_id: Optional[str] = None,
        restore_from_state: Optional[SagaState] = None,
    ):
        super().__init__(saga_id=saga_id, db_session=db_session, restore_from_state=restore_from_state)
        self.actions = DeleteAuthorActions(
            author_repo=AuthorRepository(db_session),
            bio_client=bio_client,
            author_id=author_id,
        )
        self.state.context["author_id"] = str(author_id)
        self._build_saga()

    def _build_saga(self):
        self.add_step(
            name="delete_bio",
            action=self._step_delete_bio,
            compensation=self.actions.restore_bio,
        )
        self.add_step(
            name="delete_author",
            action=self.actions.delete_author,
            compensation=self.actions.restore_author,
        )

    async def _step_delete_bio(self) -> dict:
        await self.actions.delete_bio()
        return {"bio_deleted": True}
