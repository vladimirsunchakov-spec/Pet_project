from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_, and_
from src.models.saga_state import SagaStateModel
from src.repositories.base import BaseRepository
from datetime import datetime, timedelta, timezone
from src.schemas.saga import SagaState, SagaStateUpdate, SagaStatus
from src.mappers.saga_state_mapper import SagaStateMapper
from sqlalchemy.dialects.postgresql import insert as pg_insert
import logging

logger = logging.getLogger(__name__)

class SagaStateRepository(BaseRepository[SagaStateModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, SagaStateModel)

    async def upsert_state(self, saga_id: str, saga_type: str, update_data: SagaStateUpdate) -> SagaStateModel:
        now = datetime.now(timezone.utc)

        stmt = pg_insert(SagaStateModel).values(
            saga_id=saga_id,
            saga_type=saga_type,
            status=update_data.status.value,
            current_step=update_data.current_step,
            context=update_data.context,
            error=update_data.error,
            created_at=now,
            updated_at=now,
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=[SagaStateModel.saga_id],
            set_={
                "status": stmt.excluded.status,
                "current_step": stmt.excluded.current_step,
                "context": stmt.excluded.context,
                "error": stmt.excluded.error,
                "updated_at": stmt.excluded.updated_at,
            },
        ).returning(SagaStateModel)

        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.scalar_one_or_none()

    async def get_by_saga_id(self, saga_id: str) -> Optional[SagaStateModel]:
        query = select(SagaStateModel).where(SagaStateModel.saga_id == saga_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def claim_stale_sagas(self, stale_minutes: int = 5, recovering_minutes: int = 30, limit: int = 10) -> List[SagaStateModel]:
        now = datetime.now(timezone.utc)
        stale_threshold = now - timedelta(minutes=stale_minutes)
        recovering_threshold = now - timedelta(minutes=recovering_minutes)

        stmt = (
            select(SagaStateModel)
            .where(
                or_(
                    and_(
                        SagaStateModel.status.in_([
                            SagaStatus.IN_PROGRESS.value,
                        ]),
                        SagaStateModel.updated_at < stale_threshold,
                    ),
                    and_(
                        SagaStateModel.status == SagaStatus.RECOVERING.value,
                        SagaStateModel.updated_at < recovering_threshold,
                    ),
                )
            )
            .limit(limit)
            .with_for_update(skip_locked=True)
        )

        result = await self.db.execute(stmt)
        models = list(result.scalars().all())

        if not models:
            return []

        saga_ids = [m.saga_id for m in models]
        await self.db.execute(
            update(SagaStateModel)
            .where(SagaStateModel.saga_id.in_(saga_ids))
            .values(
                status=SagaStatus.RECOVERING.value,
                updated_at=now,
            )
        )
        await self.db.flush()

        logger.info(f"Claimed {len(models)} stale sagas: {saga_ids}")

        return models
