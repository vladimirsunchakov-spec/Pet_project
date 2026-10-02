import logging
from datetime import datetime, timezone
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.clients.bio_client import BioServiceClient
from src.repositories.saga_state_repository import SagaStateRepository
from src.services.saga.delete_author_saga import DeleteAuthorSaga
from src.services.saga.create_author_saga import CreateAuthorSaga
from src.services.saga.base_saga import BaseSaga
from src.schemas.authors import AuthorCreate
from src.schemas.saga import SagaResult, SagaStatus, SagaInfo, SagaState, SagaStateUpdate
from src.mappers.saga_state_mapper import SagaStateMapper
from typing import Optional, Dict, List, Type
from uuid import uuid4, UUID

logger = logging.getLogger(__name__)


class SagaOrchestrator:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        bio_client: BioServiceClient | None = None,
    ):
        self._session_factory = session_factory
        self._bio_client = bio_client
        self._active_sagas: Dict[str, BaseSaga] = {}
        self._recovery_task: Optional[asyncio.Task] = None
        self._running = False

    def configure(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        bio_client: BioServiceClient,
    ) -> None:
        self._session_factory = session_factory
        self._bio_client = bio_client

    async def start(self) -> None:
        if self._session_factory is None or self._bio_client is None:
            raise RuntimeError("SagaOrchestrator is not configured with session_factory and bio_client")
        self._running = True
        self._recovery_task = asyncio.create_task(self._recovery_loop())
        logger.info("SagaOrchestrator started")

    async def stop(self) -> None:
        self._running = False
        if self._recovery_task:
            self._recovery_task.cancel()
            try:
                await self._recovery_task
            except asyncio.CancelledError:
                pass
        logger.info("SagaOrchestrator stopped")

    async def start_saga(self, saga_class: Type[BaseSaga], db_session: AsyncSession, **kwargs) -> SagaResult:
        if self._bio_client is None:
            raise RuntimeError("SagaOrchestrator is not configured with bio_client")

        saga_id = str(uuid4())
        saga = saga_class(
            saga_id=saga_id,
            db_session=db_session,
            bio_client=self._bio_client,
            **kwargs,
        )
        self._active_sagas[saga_id] = saga
        await self._save_state(saga, db_session)
        try:
            result = await saga.execute()
            await self._save_state(saga, db_session)
            self._active_sagas.pop(saga_id, None)
            return result
        except Exception as e:
            logger.error("Saga %s failed: %s", saga_id, e)
            try:
                await self._save_state(saga, db_session)
            except Exception as save_error:
                logger.critical(
                    "Saga %s: failed to persist FAILED state: %s",
                    saga_id,
                    save_error,
                )
            self._active_sagas.pop(saga_id, None)
            raise

    async def recover_saga(self, saga_id: str) -> Optional[SagaResult]:
        if self._session_factory is None or self._bio_client is None:
            logger.warning("SagaOrchestrator is not configured for recovery")
            return None

        async with self._session_factory() as session:
            state = await self._load_state(saga_id, session)
            if not state:
                logger.warning(f"Saga {saga_id} not found for recovery")
                return None

            if state.status in [
                SagaStatus.COMPLETED,
                SagaStatus.COMPLETED_WITH_DEFERRED,
                SagaStatus.COMPENSATED,
            ]:
                await session.commit()
                return SagaResult(
                    saga_id=saga_id,
                    status=state.status.value,
                    context=state.context,
                    error=state.error,
                    completed_at=datetime.now(timezone.utc),
                )

            saga = self._restore_saga_from_state(state, session)
            if not saga:
                logger.error("Failed to restore saga %s", saga_id)
                await session.commit()
                return None

            self._active_sagas[saga_id] = saga
            try:
                result = await saga.execute()
                await self._save_state(saga, session)
                await session.commit()
                self._active_sagas.pop(saga_id, None)
                logger.warning("Saga %s recovered", saga_id)
                return result
            except Exception as e:
                logger.error("Saga %s recovery failed: %s", saga_id, e)
                try:
                    await self._save_state(saga, session)
                    await session.commit()
                except Exception as save_error:
                    await session.rollback()
                    logger.critical(
                        "Saga %s: failed to persist FAILED state during recovery: %s",
                        saga_id,
                        save_error,
                    )
                self._active_sagas.pop(saga_id, None)
                return None

    async def cancel_saga(self, saga_id: str) -> bool:
        saga = self._active_sagas.get(saga_id)
        if not saga:
            return False

        try:
            logger.warning("Cancelling saga %s", saga_id)
            await saga._compensate(saga.state.current_step)
            if self._session_factory is not None:
                async with self._session_factory() as session:
                    await self._save_state(saga, session)
                    await session.commit()
            self._active_sagas.pop(saga_id, None)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel saga {saga_id}: {e}")
            return False

    async def get_saga_status(self, saga_id: str) -> Optional[SagaInfo]:
        if saga_id in self._active_sagas:
            saga = self._active_sagas[saga_id]
            return SagaInfo(
                saga_id=saga_id,
                saga_type=saga.__class__.__name__,
                status=saga.state.status.value,
                current_step=saga.state.current_step,
                total_steps=len(saga._steps),
                created_at=saga.state.created_at.isoformat(),
                updated_at=saga.state.updated_at.isoformat(),
                is_active=True,
                error=saga.state.error,
            )

        if self._session_factory is None:
            return None

        async with self._session_factory() as session:
            state_repo = SagaStateRepository(session)
            state_model = await state_repo.get_by_saga_id(saga_id)
            if not state_model:
                return None
            return SagaInfo(
                saga_id=state_model.saga_id,
                saga_type=state_model.saga_type,
                status=state_model.status,
                current_step=state_model.current_step,
                total_steps=0,
                created_at=state_model.created_at.isoformat(),
                updated_at=state_model.updated_at.isoformat(),
                is_active=False,
                error=state_model.error,
            )

    async def _recovery_loop(self) -> None:
        while self._running:
            try:
                stale_sagas = await self._find_stale_sagas()
                for saga_id in stale_sagas:
                    logger.warning("Recovering stale saga %s", saga_id)
                    await self.recover_saga(saga_id)
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error("Recovery loop error: %s", e)
                await asyncio.sleep(60)

    async def _find_stale_sagas(self) -> List[str]:
        if self._session_factory is None:
            return []
        try:
            async with self._session_factory() as session:
                state_repo = SagaStateRepository(session)
                claimed_models = await state_repo.claim_stale_sagas(
                    stale_minutes=5,
                    recovering_minutes=30,
                    limit=10,
                )
                saga_ids = [model.saga_id for model in claimed_models]
                await session.commit()
                return saga_ids
        except Exception as e:
            logger.error(f"Failed to claim stale sagas: {e}")
            return []

    async def _save_state(self, saga: BaseSaga, db_session: AsyncSession) -> None:
        update_data = SagaStateUpdate(
            status=saga.state.status,
            current_step=saga.state.current_step,
            context=saga.state.context,
            error=saga.state.error,
        )
        state_repo = SagaStateRepository(db_session)
        await state_repo.upsert_state(
            saga_id=saga.saga_id,
            saga_type=saga.state.saga_type,
            update_data=update_data,
        )

    async def _load_state(self, saga_id: str, db_session: AsyncSession) -> Optional[SagaState]:
        state_repo = SagaStateRepository(db_session)
        state_model = await state_repo.get_by_saga_id(saga_id)
        if not state_model:
            return None
        return SagaStateMapper.to_state(state_model)

    def _restore_saga_from_state(self, state: SagaState, db_session: AsyncSession) -> Optional[BaseSaga]:
        if self._bio_client is None:
            return None
        try:
            if state.saga_type == "CreateAuthorSaga":
                author_data = AuthorCreate.model_validate(state.context.get("author_data", {}))
                return CreateAuthorSaga(
                    db_session=db_session,
                    author_data=author_data,
                    saga_id=state.saga_id,
                    restore_from_state=state,
                    bio_client=self._bio_client,
                )
            if state.saga_type == "DeleteAuthorSaga":
                return DeleteAuthorSaga(
                    db_session=db_session,
                    author_id=UUID(state.context["author_id"]),
                    saga_id=state.saga_id,
                    restore_from_state=state,
                    bio_client=self._bio_client,
                )
            logger.warning(f"Unknown saga type {state.saga_type}")
            return None
        except Exception as e:
            logger.error(f"Failed to restore saga: {e}")
            return None


saga_orchestrator = SagaOrchestrator()
