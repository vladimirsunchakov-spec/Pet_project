from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.models.saga_state import SagaStateModel
from src.repositories.base import BaseRepository
from datetime import datetime, timedelta, timezone

class SagaStateRepository(BaseRepository[SagaStateModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, SagaStateModel)

    async def save_state(self, saga_id: str, state: dict) -> None:
        existing = await self.get_by_saga_id(saga_id)

        if existing:
            stmt = (
                update(SagaStateModel)
                .where(SagaStateModel.saga_id == saga_id)
                .values(
                    status=state["status"],
                    current_step=state["current_step"],
                    context=state["context"],
                    error=state.get("error"),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            await self.db.execute(stmt)
        else:
            saga_state = SagaStateModel(
                saga_id=saga_id,
                saga_type=state["saga_type"],
                status=state["status"],
                current_step=state["current_step"],
                context=state["context"],
                error=state.get("error"),
            )
            self.db.add(saga_state)

        await self.db.flush()

    async def get_by_saga_id(self, saga_id: str) -> Optional[SagaStateModel]:
        query = select(SagaStateModel).where(SagaStateModel.saga_id == saga_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_stale_saga(self, minutes: int = 5) -> list[SagaStateModel]:
        threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes)

        query = select(SagaStateModel).where(
            SagaStateModel.status.in_(["in_progress", "pending"]),
            SagaStateModel.updated_at < threshold
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

