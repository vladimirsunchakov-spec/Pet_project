from uuid import UUID
from typing import Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.bio_client import BioServiceClient
from src.config import settings
from src.exceptions import ExternalServiceUnavailableError, ExternalServiceError
from src.repositories.author_repository import AuthorRepository
from src.repositories.task_repository import TaskRepository
from src.schemas.authors import AuthorCreate
from src.schemas.bio import BioCreateRequest
from src.schemas.saga import SagaState, SagaStepOutcome, SagaStepOutcomeStatus
from src.services.author.base_saga import BaseSaga

logger = logging.getLogger(__name__)


class CreateAuthorSaga(BaseSaga):
    def __init__(
        self,
        db_session: AsyncSession,
        author_data: AuthorCreate,
        bio_client: BioServiceClient,
        restore_from_state: Optional[SagaState] = None,
        saga_id: Optional[str] = None,
    ):
        super().__init__(saga_id=saga_id, db_session=db_session, restore_from_state=restore_from_state)
        self._author_data = author_data
        self._author_repo = AuthorRepository(db_session)
        self._task_repo = TaskRepository(db_session)
        self._bio_client = bio_client
        self.state.context["author_data"] = author_data.model_dump(mode="json")
        self._build_saga()

    def _build_saga(self) -> None:
        self.add_step(
            name="create_author",
            action=self._step_create_author,
            compensation=self._compensate_author,
        )
        self.add_step(
            name="create_bio",
            action=self._step_create_bio,
            compensation=self._compensate_bio,
        )

    async def _step_create_author(self) -> SagaStepOutcome:
        author = self._author_data.to_model()
        created_author = await self._author_repo.create_author(author)
        self.state.context["author_id"] = str(created_author.id)
        return SagaStepOutcome(
            status=SagaStepOutcomeStatus.SUCCESS,
            data={"author_id": str(created_author.id)},
        )

    async def _step_create_bio(self) -> SagaStepOutcome:
        author_id = UUID(self.state.context["author_id"])
        idempotency_key = self.state.context["idempotency_key"]
        request = BioCreateRequest(
            author_id=author_id,
            rating=settings.bio_default_rating,
            awards_count=settings.bio_default_awards_count,
        )
        try:
            bio_data = await self._bio_client.create_bio(
                request=request,
                idempotency_key=idempotency_key,
            )
            self.state.context["bio_data"] = bio_data.model_dump(mode="json")
            return SagaStepOutcome(
                status=SagaStepOutcomeStatus.SUCCESS,
                data={"bio": bio_data.model_dump(mode="json")},
            )
        except ExternalServiceUnavailableError as e:
            logger.warning(
                "Bio service unavailable, scheduling create_bio task for author %s: %s",
                author_id,
                e,
            )
            await self._task_repo.create_task(
                task_type="create_bio",
                payload={
                    "author_id": str(author_id),
                    "rating": settings.bio_default_rating,
                    "awards_count": settings.bio_default_awards_count,
                    "saga_id": self.saga_id,
                    "idempotency_key": idempotency_key,
                },
            )
            return SagaStepOutcome(
                status=SagaStepOutcomeStatus.DEFERRED,
                data={"scheduled_in_worker": True},
            )
        except ExternalServiceError:
            raise

    async def _compensate_author(self) -> None:
        author_id = UUID(self.state.context["author_id"])
        await self._author_repo.soft_delete(author_id)

    async def _compensate_bio(self) -> None:
        author_id = UUID(self.state.context["author_id"])
        try:
            await self._bio_client.update_bio_status(
                author_id=author_id,
                status=settings.bio_deleted_status,
                idempotency_key=f"{self.state.context['idempotency_key']}:compensate",
            )
        except ExternalServiceUnavailableError:
            raise
        except ExternalServiceError as e:
            logger.warning(
                "Bio compensation failed for author %s: %s",
                author_id,
                e,
            )
