from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from services.saga.base_saga import BaseSaga
from src.services.actions.delete_author_actions import DeleteAuthorActions
import logging

logger = logging.getLogger(__name__)

class DeleteAuthorSaga(BaseSaga):
    def __init__(self, db_session: AsyncSession, author_id: UUID, saga_id: Optional[str] = None):
        super().__init__(saga_id)
        self.db_session = db_session
        self.author_id = author_id
        self.actions = DeleteAuthorActions(db_session, author_id)
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

    async def _step_delete_bio(self) -> bool:
        result = await self.actions.delete_bio()
        return {"bio deleted": result}

    async def _step_delete_author(self) -> dict:
        result = await self.actions.delete_author()
        return {"author deleted": result}

    async def _compensate_restore_bio(self):
        await self.actions.restore_bio()

    async def _compensate_restore_author(self):
        await self.actions.restore_author()



