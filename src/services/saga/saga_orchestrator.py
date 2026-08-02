from typing import Optional, Dict, List, Type
from uuid import UUID, uuid4
import logging
from datetime import datetime, timedelta
import asyncio

from services.saga.base_saga import SagaStatus, SagaState
from src.services.saga.base_saga import BaseSaga
from src.services.saga.create_author_saga import CreateAuthorSaga
from src.services.saga.delete_author_saga import DeleteAuthorSaga

logger = logging.getLogger(__name__)

class SagaOrchestrator():
    _active_sagas : Dict[str, BaseSaga] = {}
    _saga_state: Dict[str, dict] = {}

    def __init__(self):
        self._recovery_task: Optional[asyncio.Task] = None
        self._running = False

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

    async def start_saga(
        self,
        saga_class: Type[BaseSaga],
        **kwargs
    ) -> dict:
        saga_id = str(uuid4())
        saga = saga_class(saga_id=saga_id, **kwargs)

        self._active_sagas[saga_id] = saga
        self._save_state(saga)

        try:
            logger.info(f"Starting saga {saga_id} of type {saga.__class__.__name__}")
            result = await saga.execute()
            self._save_state(saga)
            self._active_sagas.pop(saga_id, None)
            logger.info(f"Saga {saga_id} completed successfully")
            return result

        except Exception as e:
            logger.error(f"Saga {saga_id} failed: {e}")
            self._save_state(saga)
            self._active_sagas.pop(saga_id, None)
            raise

    async def recover_saga(self, saga_id: str) -> Optional[dict]:
        state = self._load_state(saga_id)
        if not state:
            logger.warning(f"Saga {saga_id} not found for recovery")
            return None

        if state["status"] in [SagaStatus.COMPLETED.value, SagaStatus.COMPENSATED.value]:
            logger.info(f"Saga {saga_id} already completed/compensated")
            return state

        saga = self._restore_saga_from_state(state)
        if not saga:
            logger.error(f"Failed to restore saga {saga_id}")
            return None

        self._active_sagas[saga_id] = saga

        try:
            result = await saga.execute()
            self._save_state(saga)
            self._active_sagas.pop(saga_id, None)
            logger.info(f"Saga {saga_id} recovered successfully")
            return result

        except Exception as e:
            logger.error(f"Saga {saga_id} recovery failed: {e}")
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
            self._save_state(saga)
            self._active_sagas.pop(saga_id, None)
            return True

        except Exception as e:
            logger.error(f"Failed to cancel saga {saga_id}: {e}")
            return False

    def get_saga_status(self, saga_id: str) -> Optional[dict]:
        if saga_id in self._active_sagas:
            saga = self._active_sagas[saga_id]
            return {
                "saga_id": saga_id,
                "status": saga.state.status.value,
                "current_step": saga.state.current_step,
                "total_steps": len(saga._steps),
                "created_at": saga.state.created_at.isoformat(),
                "updated_at": saga.state.updated_at.isoformat(),
                "context": saga.state.context,
                "is_active": True
            }

        state = self._load_state(saga_id)
        if state:
            return {
                "saga_id": saga_id,
                "status": state["status"],
                "current_step": state.get("current_step", 0),
                "created_at": state.get("created_at"),
                "updated_at": state.get("updated_at"),
                "is_active": False
            }

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

        for saga_id, state in list(self._saga_state.items())[-100:]:
            if saga_id not in self._active_sagas:
                sagas.append({
                    "saga_id": saga_id,
                    "type": state.get("saga_type", "Unknown"),
                    "status": state.get("status", "unknow"),
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
                break
            except Exception as e:
                logger.error(f"Recovery loop error: {e}")
                await asyncio.sleep(60)

    async def _find_stale_sagas(self) -> List[str]:
        stale_sagas = []
        now = datetime.now()

        for saga_id, state in self._saga_states.items():
            if state.get("status") in [
                SagaStatus.IN_PROGRESS.value,
                SagaStatus.PENDING.value,
            ]:
                updated_at = state.get("updated_at")
                if updated_at:
                    updated_at = datetime.fromisoformat(updated_at)
                    if (now - updated_at) > timedelta(minutes=5):
                        stale_sagas.append(saga_id)

        return stale_sagas

    def _save_state(self, saga: BaseSaga):
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

    def _load_state(self, saga_id: str) -> Optional[dict]:
        return self._saga_states.get(saga_id)

    def _restore_saga_from_state(self, state: dict) -> Optional[BaseSaga]:
        try:
            saga_type = state.get("saga_type")
            context = state.get("context", {})

            if saga_type == "CreateAuthorSaga":
                return None
            elif saga_type == "DeleteAuthorSaga":
                return None
            else:
                logger.warning(f"Unknown saga type {saga_type}")
                return None

        except Exception as e:
            logger.error(f"Failed to restore saga: {e}")
            return None

saga_orchestrator = SagaOrchestrator()





