from typing import Optional, Any, Dict, Callable, Awaitable, List
from uuid import UUID, uuid4
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.saga import SagaStatus, SagaStep, SagaState, SagaStepStatus, SagaResult
from src.repositories.saga_state_repository import SagaStateRepository

logger = logging.getLogger(__name__)

class BaseSaga:
    def __init__(
        self,
        saga_id: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
        restore_from_state: Optional[SagaState] = None,
    ):
        self.saga_id = saga_id or str(uuid4())
        self._state_repo = SagaStateRepository(db_session) if db_session else None

        if restore_from_state:
            self.state = restore_from_state
            self._steps: List[SagaStep] = []
            self._current_step_index = self.state.current_step
            logger.info(
                f"Saga {self.saga_id}: Restored from state,"
                f"current step: {self.state.current_step},"
                f"status: {self.state.status}"
            )
        else:
            self.state = SagaState(
                saga_id=self.saga_id,
                saga_type=self.__class__.__name__,
            )
            self._steps: List[SagaStep] = []
            self._current_step_index = 0

    def add_step(
        self,
        name: str,
        action: Callable[[], Awaitable[Any]],
        compensation: Optional[Callable[[], Awaitable[None]]] = None
    ) -> "BaseSaga":
        step = SagaStep(
            id=len(self._steps) + 1,
            name=name,
            action=action,
            compensation=compensation,
        )
        self._steps.append(step)
        return self

    async def execute(self) -> SagaResult:
        if self.state.status in [SagaStatus.COMPLETED, SagaStatus.COMPENSATED]:
            logger.info(f"Saga {self.saga_id}: Already {self.state.status}")
            return SagaResult(
                saga_id=self.saga_id,
                status=self.state.status.value,
                context=self.state.context,
                error=self.state.error,
                completed_at=datetime.now(timezone.utc)
            )
        self.state.status = SagaStatus.IN_PROGRESS
        await self._save_state()

        compensation_done = False

        try:
            start_idx = self.state.current_step

            for idx in range(start_idx, len(self._steps)):
                step = self._steps[idx]
                self._current_step_index = idx
                self.state.current_step = idx
                logger.info(f"Saga {self.saga_id}: Executing step {idx+1}/{len(self._steps)} - {step.name}")

                if step.status == SagaStepStatus.SUCCESS:
                    logger.info(f"Saga {self.saga_id}: Step {step.name} already completed, skipping")
                    continue

                step.status = SagaStepStatus.EXECUTING
                await self._save_state()

                try:
                    result = await step.action()
                    step.status = SagaStepStatus.SUCCESS
                    step.result = result
                    await self._save_state()
                    logger.info(f"Saga {self.saga_id}: Step {step.name} completed successfully")
                except Exception as e:
                    step.status = SagaStepStatus.FAILED
                    step.error = str(e)
                    logger.error(f"Saga {self.saga_id}: Step {step.name} failed {e}")
                    await self._compensate(idx)
                    compensation_done = True
                    return SagaResult(
                        saga_id=self.saga_id,
                        status=self.state.status.value,
                        context=self.state.context,
                        error=self.state.error,
                        completed_at=datetime.now(timezone.utc),
                    )

            self.state.status = SagaStatus.COMPLETED
            await self._save_state()

            logger.info(f"Saga {self.saga_id}: Completed successfully")
            return SagaResult(
                saga_id=self.saga_id,
                status="completed",
                context=self.state.context,
                completed_at=datetime.now(timezone.utc)
            )

        except Exception as e:
            if not compensation_done:
                self.state.status = SagaStatus.FAILED
                self.state.error = str(e)
                await self._save_state()
            return SagaResult(
                saga_id=self.saga_id,
                status=self.state.status.value,
                context=self.state.context,
                error=self.state.error,
                completed_at=datetime.now(timezone.utc)
            )

    async def _compensate(self, failed_step_index: int):
        self.state.status = SagaStatus.COMPENSATING
        await self._save_state()
        logger.info(f"Saga {self.saga_id}: Starting compensation from step {failed_step_index}")

        compensation_failed = False

        for idx in range(failed_step_index -1, -1, -1):
            step = self._steps[idx]
            if step.status == SagaStepStatus.SUCCESS and step.compensation:
                try:
                    logger.info(f"Saga {self.saga_id}: Compensating step {idx + 1} - {step.name}")
                    await step.compensation()
                    step.status = SagaStepStatus.COMPENSATED
                    await self._save_state()
                except Exception as e:
                    logger.error(f"Saga {self.saga_id}: Compensation failed for step {step.name}: {e}")
                    self.state.error = f"Compensation failed for step {step.name}: {e}"
                    compensation_failed = True
                    break
        if compensation_failed:
            self.state.status = SagaStatus.COMPENSATION_FAILED
            await self._save_state()
            logger.error(f"Saga {self.saga_id}: Compensation failed")
            raise Exception(f"Compensation failed: {self.state.error}")

        self.state.status = SagaStatus.COMPENSATED
        await self._save_state()
        logger.info(f"Saga {self.saga_id}: Compensation completed")

    async def _save_state(self):
        self.state.updated_at = datetime.now(timezone.utc)

        if self._state_repo:
            try:
                state_data = {
                    "saga_id": self.saga_id,
                    "saga_type": self.state.saga_type,
                    "status": self.state.status.value,
                    "current_step": self.state.current_step,
                    "context": self.state.context,
                    "error": self.state.error,
                }
                await self._state_repo.save_state(self.saga_id, state_data)
                logger.debug(f"Saga {self.saga_id}: Saving state to DB - {self.state.status}")
            except Exception as e:
                logger.error(f"Saga {self.saga_id}: Failed to save state: {e}")
        else:
            logger.warning(f"Saga {self.saga_id}: No state repo available")

    def get_state(self) ->SagaState:
        return self.state

