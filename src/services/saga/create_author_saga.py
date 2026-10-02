from uuid import UUID
from typing import Optional

from src.repositories.task_repository import TaskRepository
from src.services.saga.base_saga import BaseSaga
from src.services.actions.create_author_actions import CreateAuthorActions
from src.repositories.author_repository import AuthorRepository
from src.clients.bio_client import BioServiceClient
from src.schemas.authors import AuthorCreate
from src.schemas.saga import SagaState
from sqlalchemy.ext.asyncio import AsyncSession


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
        self.author_data = author_data
        self.actions = CreateAuthorActions(
            author_repo=AuthorRepository(db_session),
            bio_client=bio_client,
            task_repo=TaskRepository(db_session),
            author_data=author_data,
        )
        self.state.context["author_data"] = author_data.model_dump(mode="json")
        self._build_saga()

    def _build_saga(self):
        self.add_step(
            name="create_author",
            action=self._step_create_author,
            compensation=lambda: self.actions.compensate_author(UUID(self.state.context["author_id"])),
        )
        self.add_step(
            name="create_bio",
            action=self._step_create_bio,
            compensation=lambda: self.actions.compensate_bio(UUID(self.state.context["author_id"])),
        )

    async def _step_create_author(self) -> dict:
        result = await self.actions.create_author()
        self.state.context["author_id"] = result["author_id"]
        return result

    async def _step_create_bio(self) -> dict:
        author_id = UUID(self.state.context["author_id"])
        idempotency_key = self.state.context["idempotency_key"]
        result = await self.actions.create_bio(author_id, idempotency_key=idempotency_key)
        if result and result.get("bio_data"):
            bio_data = result["bio_data"]
            self.state.context["bio_data"] = (
                bio_data.model_dump(mode="json")
                if hasattr(bio_data, "model_dump")
                else bio_data
            )
        return result
