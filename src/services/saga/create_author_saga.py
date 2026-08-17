from uuid import UUID
from typing import Optional
from src.services.saga.base_saga import BaseSaga
from src.services.actions.create_author_actions import CreateAuthorActions
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

class CreateAuthorSaga(BaseSaga):
    def __init__(
        self,
        db_session: AsyncSession,
        author_data: dict,
        saga_id: Optional[str] = None
    ):
        super().__init__(saga_id)
        self.db_session = db_session
        self.author_data = author_data
        self.actions = CreateAuthorActions(db_session, author_data)
        self.state.context["author_data"] = author_data
        self._build_saga()

    def _build_saga(self):
        self.add_step(
            name="create_author",
            action=self._step_create_author,
            compensation=self._compensate_author
        )

        self.add_step(
            name="create_bio",
            action=self._step_create_bio,
            compensation=self._compensate_bio
        )

    async def _step_create_author(self) -> dict:
        result = await self.actions.create_author()
        self.state.context["author_data"] = result["author_id"]
        return result

    async def _step_create_bio(self) -> dict:
        author_id = UUID(self.state.context["author_id"])
        result = await self.actions.create_bio(author_id)
        self.state.context["bio_data"] = result.get["bio_data"]
        return result

    async def _compensate_author(self):
        author_id = self.state.context.get("author_id")
        if author_id:
            await self.actions.compensate_author(UUID(author_id))

    async def _compensate_bio(self):
        author_id = self.state.context.get("author_id")
        if author_id:
            await self.actions.compensate_bio(UUID(author_id))
