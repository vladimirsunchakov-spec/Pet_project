import logging
from datetime import datetime, timezone
import asyncio
from src.repositories.task_repository import TaskRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.clients.bio_client import BioServiceClient
from src.repositories.author_repository import AuthorRepository
from src.repositories.saga_state_repository import SagaStateRepository
from src.services.author.delete.delete_author_saga import DeleteAuthorSaga
from src.services.author.create.create_author_saga import CreateAuthorSaga
from src.services.author.shared.base_saga import BaseSaga
from src.schemas.saga import SagaResult, SagaStatus, SagaInfo, SagaState, SagaStateUpdate
from typing import Optional, Dict, List
from uuid import uuid4, UUID


logger = logging.getLogger(__name__)

class SagaOrchestrator:
    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db_session = db_session
        self._state_repo = SagaStateRepository(db_session) if db_session else None
        self._active_sagas: Dict[str, BaseSaga] = {}
        self._saga_states: Dict[str, dict] = {}
        self._recovery_task: Optional[asyncio.Task] = None
        self._running = False
        self._author_repo = AuthorRepository(db_session) if db_session else None
        self._bio_client = BioServiceClient()
        self._task_repo = TaskRepository(db_session) if db_session else None

    async def start(self):
        self._running = True
        self._recovery_task = asyncio.create_task(self._recovery_loop())
        logger.info("SagaOrchestrator started")

    async def stop(self):
        self._running = False
        if self._recovery_task:
            self._recovery_task.cancel()
            try:
                await self._recovery_task
            except asyncio.CancelledError:
                pass
        logger.info("SagaOrchestrator stopped")

    async def start_saga(self, saga_class, **kwargs) -> SagaResult:
        saga_id = str(uuid4())
        saga = saga_class(
            saga_id=saga_id,
            db_session=self.db_session,
            author_repo=self._author_repo,
            bio_client=self._bio_client,
            task_repo=self._task_repo,
            **kwargs,
        )
        self._active_sagas[saga_id] = saga
        await self._save_state(saga)
        try:
            logger.info(f"Starting saga {saga_id} of type {saga.__class__.__name__}")
            result = await saga.execute()

            await self._save_state(saga)

            self._active_sagas.pop(saga_id, None)
            logger.info(f"Saga {saga_id} completed with status {result.status}")
            return result

        except Exception as e:
            logger.error(f"Saga {saga_id} failed: {e}")
            try:
                await self._save_state(saga)
            except Exception as save_error:
                logger.critical(
                    f"Saga {saga_id}: Critical - failed to save "
                    f"Failed state: {save_error}")
            self._active_sagas.pop(saga_id, None)
            raise

    async def recover_saga(self, saga_id: str) -> Optional[SagaResult]:
        state = await self._load_state(saga_id)
        if not state:
            logger.warning(f"Saga {saga_id} not found for recovery")
            return None

        if state["status"] in [SagaStatus.COMPLETED.value, SagaStatus.COMPLETED_WITH_DEFERRED.value, SagaStatus.COMPENSATED.value]:
            logger.info(f"Saga {saga_id} already completed/compensated")
            return SagaResult(
                saga_id=saga_id,
                status=state["status"],
                context=state.get("context", {}),
                error=state.get("error"),
                completed_at=datetime.now(timezone.utc),
            )

        saga = await self._restore_saga_from_state(state)
        if not saga:
            logger.error(f"Failed to restore saga {saga_id}")
            return None

        self._active_sagas[saga_id] = saga

        try:
            result = await saga.execute()

            await self._save_state(saga)

            self._active_sagas.pop(saga_id, None)
            logger.info(f"Saga {saga_id} recovered successfully")
            return result

        except Exception as e:
            logger.error(f"Saga {saga_id} recovery failed: {e}")
            try:
                await self._save_state(saga)
            except Exception as save_error:
                logger.critical(
                    f"Saga {saga_id}: Critical - failed to save "
                    f"Failed state during recovery: {save_error}"
                )
            self._active_sagas.pop(saga_id, None)
            return None

    async def cancel_saga(self, saga_id: str) -> bool:
        saga = self._active_sagas.get(saga_id)
        if not saga:
            logger.warning(f"Saga {saga_id} not active")
            return False

        try:
            logger.info(f"Cancelling saga {saga_id}")
            await saga._compensate(saga.state.current_step)
            await self._save_state(saga)
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

        state = self._saga_states.get(saga_id)
        if state:
            return SagaInfo(
                saga_id=saga_id,
                saga_type=state.get("saga_type", "Unknown"),
                status=state.get("status", "Unknown"),
                current_step=state.get("current_step", 0),
                total_steps=len(state.get("steps", [])),
                created_at=state.get("created_at", ""),
                updated_at=state.get("updated_at", ""),
                is_active=False,
                error=state.get("error")
            )
        if self._state_repo:
            try:
                state_model = await self._state_repo.get_by_saga_id(saga_id)
                if state_model:
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
            except Exception as e:
                logger.error(f"Failed to get saga from DB: {e}")
        return None

    def get_all_sagas(self) -> List[dict]:
        sagas = []
        for saga_id, saga in self._active_sagas.items():
            sagas.append({
                "saga_id": saga_id,
                "type": saga.__class__.__name__,
                "status": saga.state.status.value,
                "current_step": saga.state.current_step,
                "is_active": True,
                "created_at": saga.state.created_at.isoformat()
            })

        for saga_id, state in list(self._saga_states.items())[-100:]:
            if saga_id not in self._active_sagas:
                sagas.append({
                    "saga_id": saga_id,
                    "type": state.get("saga_type", "Unknown"),
                    "status": state.get("status", "unknown"),
                    "is_active": False,
                    "created_at": state.get("created_at")
                })

        return sagas

    async def _recovery_loop(self):
        while self._running:
            try:
                stale_sagas = await self._find_stale_sagas()

                for saga_id in stale_sagas:
                    logger.info(f"Recovering stale saga {saga_id}")
                    await self.recover_saga(saga_id)

                await asyncio.sleep(60)

            except asyncio.CancelledError:
                logger.info("Recovery loop cancelled")
                raise

            except Exception as e:
                logger.error(f"Recovery loop error: {e}")
                await asyncio.sleep(60)

    async def _find_stale_sagas(self) -> List[str]:
        if not self._state_repo:
            logger.warning("No state repository available for stale saga search")
            return []

        try:
            claimed_models = await self._state_repo.claim_stale_sagas(
                stale_minutes=5,
                recovering_minutes=30,
                limit=10,
            )
            return [model.saga_id for model in claimed_models]
        except Exception as e:
            logger.error(f"Failed to claim stale sagas: {e}")
            return []

    async def _save_state(self, saga: BaseSaga):
        state = {
            "saga_id": saga.saga_id,
            "saga_type": saga.__class__.__name__,
            "status": saga.state.status.value,
            "current_step": saga.state.current_step,
            "steps": [
                {
                    "id": step.id,
                    "name": step.name,
                    "status": step.status.value,
                    "error": step.error
                }
                for step in saga._steps
            ],
            "context": saga.state.context,
            "error": saga.state.error,
            "created_at": saga.state.created_at.isoformat(),
            "updated_at": saga.state.updated_at.isoformat(),
        }

        self._saga_states[saga.saga_id] = state

        if not self._state_repo:
            return

        try:
            update_data = SagaStateUpdate(
                status=saga.state.status,
                current_step=saga.state.current_step,
                context=saga.state.context,
                error=saga.state.error,
            )
            await self._state_repo.upsert_state(
                saga_id=saga.saga_id,
                saga_type=saga.state.saga_type,
                update_data=update_data,
                )
        except Exception as e:
            logger.error(f"Failed to save state to DB: {e}")
            raise

    async def _load_state(self, saga_id: str) -> Optional[dict]:
        state = self._saga_states.get(saga_id)
        if state:
            return state

        if self._state_repo:
            try:
                state_model = await self._state_repo.get_by_saga_id(saga_id)
                if state_model:
                    state = {
                        "saga_id": state_model.saga_id,
                        "saga_type": state_model.saga_type,
                        "status": state_model.status,
                        "current_step": state_model.current_step,
                        "context": state_model.context,
                        "error": state_model.error,
                        "created_at": state_model.created_at.isoformat(),
                        "updated_at": state_model.updated_at.isoformat(),
                        "steps": [],
                    }
                    self._saga_states[saga_id] = state
                    return state
            except Exception as e:
                logger.error(f"Failed to load state from DB: {e}")
        return None

    async def _restore_saga_from_state(self, state: dict) -> Optional[BaseSaga]:
        try:
            saga_type = state.get("saga_type")
            context = state.get("context", {})

            saga_state = SagaState(
                saga_id=state["saga_id"],
                saga_type=state["saga_type"],
                status=SagaStatus(state["status"]),
                current_step=state["current_step"],
                context=state.get("context", {}),
                error=state.get("error"),
                created_at=datetime.fromisoformat(state["created_at"]),
                updated_at=datetime.fromisoformat(state["updated_at"]),
            )

            if saga_type == "CreateAuthorSaga":
                return CreateAuthorSaga(
                    db_session=self.db_session,
                    author_data=context.get("author_data", {}),
                    saga_id=state["saga_id"],
                    restore_from_state=saga_state,
                    author_repo=self._author_repo,
                    bio_client=self._bio_client,
                    task_repo=self._task_repo,
                )
            elif saga_type == "DeleteAuthorSaga":
                return DeleteAuthorSaga(
                    db_session=self.db_session,
                    author_id=UUID(context.get("author_id")),
                    saga_id=state["saga_id"],
                    restore_from_state=saga_state,
                    author_repo=self._author_repo,
                    bio_client=self._bio_client,
                )
            else:
                logger.warning(f"Unknown saga type {saga_type}")
                return None

        except Exception as e:
            logger.error(f"Failed to restore saga: {e}")
            return None

saga_orchestrator = SagaOrchestrator()





