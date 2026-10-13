from uuid import UUID
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.bio_client import BioServiceClient
from src.config import settings
from src.exceptions import (
    ExternalServiceError,
    ExternalServiceUnavailableError,
    NotFoundError,
)
from src.repositories.author_repository import AuthorRepository
from src.schemas.saga import SagaState, SagaStepOutcome, SagaStepOutcomeStatus
from src.services.author.base_saga import BaseSaga


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
        self._author_id = author_id
        self._author_repo = AuthorRepository(db_session)
        self._bio_client = bio_client
        self.state.context["author_id"] = str(author_id)
        if "idempotency_key" not in self.state.context:
            self.state.context["idempotency_key"] = self.saga_id
        self._build_saga()

    def _build_saga(self) -> None:
        self.add_step(
            name="delete_bio",
            action=self._step_delete_bio,
            compensation=self._restore_bio,
        )
        self.add_step(
            name="delete_author",
            action=self._step_delete_author,
            compensation=self._restore_author,
        )

    async def _step_delete_bio(self) -> SagaStepOutcome:
        try:
            await self._bio_client.update_bio_status(
                author_id=self._author_id,
                status=settings.bio_deleted_status,
                idempotency_key=f"{self.state.context['idempotency_key']}:delete",
            )
            return SagaStepOutcome(status=SagaStepOutcomeStatus.SUCCESS, data={"bio_deleted": True})
        except NotFoundError:
            return SagaStepOutcome(status=SagaStepOutcomeStatus.SUCCESS, data={"bio_deleted": False})
        except (ExternalServiceUnavailableError, ExternalServiceError):
            raise

    async def _step_delete_author(self) -> SagaStepOutcome:
        deleted = await self._author_repo.soft_delete(self._author_id)
        if not deleted:
            raise NotFoundError("Author", str(self._author_id))
        return SagaStepOutcome(status=SagaStepOutcomeStatus.SUCCESS, data={"author_deleted": True})

    async def _restore_bio(self) -> None:
        await self._bio_client.update_bio_status(
            author_id=self._author_id,
            status=settings.bio_active_status,
            idempotency_key=f"{self.state.context['idempotency_key']}:restore",
        )

    async def _restore_author(self) -> None:
        await self._author_repo.restore(self._author_id)
