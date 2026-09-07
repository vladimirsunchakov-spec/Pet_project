from uuid import UUID
from typing import Optional
from .base_saga import BaseSaga
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
            compensation=lambda: self.actions.compensate_author(UUID(self.state.context["author_id"]))
        )

        self.add_step(
            name="create_bio",
            action=self._step_create_bio,
            compensation=lambda: self.actions.compensate_bio(UUID(self.state.context["author_id"]))
        )

    async def _step_create_author(self) -> dict:
        result = await self.actions.create_author()
        self.state.context["author_id"] = result["author_id"]
        logger.info(f"Author created with id {result['author_id']}")
        return result

    async def _step_create_bio(self) -> dict:
        author_id = UUID(self.state.context["author_id"])
        logger.info(f"Creating bio for author {author_id}")
        result = await self.actions.create_bio(author_id)

        if result and result.get("bio_data"):
            self.state.context["bio_data"] = result["bio_data"]

        return result

