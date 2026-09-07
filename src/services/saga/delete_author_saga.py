from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.saga import SagaState
from .base_saga import BaseSaga
from src.services.actions.delete_author_actions import DeleteAuthorActions
import logging

logger = logging.getLogger(__name__)

class DeleteAuthorSaga(BaseSaga):
    def __init__(self, db_session: AsyncSession, author_id: UUID, saga_id: Optional[str] = None, restore_from_state: Optional[SagaState] = None):
        super().__init__(saga_id, db_session, restore_from_state)
        self.db_session = db_session
        self.author_id = author_id
        self.actions = DeleteAuthorActions(db_session, author_id)
        self.state.context["author_id"] = str(author_id)
        self._build_saga()

    def _build_saga(self):
        self.add_step(
            name="delete_bio",
            action=self.actions.delete_bio,
            compensation=self.actions.restore_bio
        )
        self.add_step(
            name="delete_author",
            action=self.actions.delete_author,
            compensation=self.actions.restore_author
        )

