from typing import Optional, Callable, Awaitable, List
from uuid import uuid4
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.saga import (
    SagaStatus,
    SagaStep,
    SagaState,
    SagaStepStatus,
    SagaResult,
    SagaStateUpdate,
    SagaStepOutcome,
    SagaStepOutcomeStatus,
)
from src.repositories.saga_state_repository import SagaStateRepository

logger = logging.getLogger(__name__)

_TERMINAL_STATUSES = {
    SagaStatus.COMPLETED,
    SagaStatus.COMPENSATED,
    SagaStatus.FAILED,
    SagaStatus.COMPENSATION_FAILED,
}


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
        else:
            self.state = SagaState(
                saga_id=self.saga_id,
                saga_type=self.__class__.__name__,
            )
            self.state.context["idempotency_key"] = str(uuid4())
            self._steps: List[SagaStep] = []
            self._current_step_index = 0

    def add_step(
        self,
        name: str,
        action: Callable[[], Awaitable[SagaStepOutcome]],
        compensation: Optional[Callable[[], Awaitable[None]]] = None,
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
        if self.state.status in _TERMINAL_STATUSES:
            return SagaResult(
                saga_id=self.saga_id,
                status=self.state.status.value,
                context=self.state.context,
                error=self.state.error,
                completed_at=datetime.now(timezone.utc),
            )

        if self.state.status == SagaStatus.WAITING_DEFERRED:
            return SagaResult(
                saga_id=self.saga_id,
                status=self.state.status.value,
                context=self.state.context,
                error=self.state.error,
                completed_at=datetime.now(timezone.utc),
            )

        self.state.status = SagaStatus.IN_PROGRESS
        await self._save_state()

        compensation_done = False
        has_deferred = False

        try:
            start_idx = self.state.current_step

            for idx in range(start_idx, len(self._steps)):
                step = self._steps[idx]
                self._current_step_index = idx

                step.status = SagaStepStatus.EXECUTING
                await self._save_state()

                try:
                    outcome = await step.action()
                    if not isinstance(outcome, SagaStepOutcome):
                        raise TypeError(
                            f"Step {step.name} must return SagaStepOutcome, got {type(outcome)!r}"
                        )

                    if outcome.status == SagaStepOutcomeStatus.DEFERRED:
                        step.status = SagaStepStatus.DEFERRED
                        step.result = outcome.data
                        has_deferred = True
                        logger.warning(
                            "Saga %s: step %s deferred",
                            self.saga_id,
                            step.name,
                        )
                    else:
                        step.status = SagaStepStatus.SUCCESS
                        step.result = outcome.data

                    self.state.current_step = idx + 1
                    await self._save_state()

                except Exception as e:
                    step.status = SagaStepStatus.FAILED
                    step.error = str(e)
                    logger.error("Saga %s: step %s failed: %s", self.saga_id, step.name, e)
                    await self._compensate(idx)
                    compensation_done = True
                    return SagaResult(
                        saga_id=self.saga_id,
                        status=self.state.status.value,
                        context=self.state.context,
                        error=self.state.error,
                        completed_at=datetime.now(timezone.utc),
                    )

            if has_deferred:
                self.state.status = SagaStatus.WAITING_DEFERRED
            else:
                self.state.status = SagaStatus.COMPLETED
            await self._save_state()

            return SagaResult(
                saga_id=self.saga_id,
                status=self.state.status.value,
                context=self.state.context,
                completed_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            if not compensation_done:
                self.state.status = SagaStatus.FAILED
                self.state.error = str(e)
                try:
                    await self._save_state()
                except Exception as save_error:
                    logger.critical(
                        "Saga %s: failed to persist FAILED state: %s",
                        self.saga_id,
                        save_error,
                    )

            return SagaResult(
                saga_id=self.saga_id,
                status=self.state.status.value,
                context=self.state.context,
                error=self.state.error,
                completed_at=datetime.now(timezone.utc),
            )

    async def _compensate(self, failed_step_index: int):
        self.state.status = SagaStatus.COMPENSATING
        await self._save_state()
        logger.warning(
            "Saga %s: starting compensation from step %s",
            self.saga_id,
            failed_step_index,
        )

        compensation_failed = False

        for idx in range(failed_step_index - 1, -1, -1):
            step = self._steps[idx]
            if step.status in [SagaStepStatus.SUCCESS, SagaStepStatus.FAILED] and step.compensation:
                try:
                    await step.compensation()
                    step.status = SagaStepStatus.COMPENSATED
                    await self._save_state()
                except Exception as e:
                    logger.error(
                        "Saga %s: compensation failed for step %s: %s",
                        self.saga_id,
                        step.name,
                        e,
                    )
                    self.state.error = f"Compensation failed for {step.name}: {e}"
                    compensation_failed = True
                    break

        if compensation_failed:
            self.state.status = SagaStatus.COMPENSATION_FAILED
            await self._save_state()
            raise Exception(f"Compensation failed: {self.state.error}")

        self.state.status = SagaStatus.COMPENSATED
        await self._save_state()

    async def _save_state(self):
        self.state.updated_at = datetime.now(timezone.utc)

        if not self._state_repo:
            logger.warning("Saga %s: no state repo available", self.saga_id)
            return
        try:
            update_data = SagaStateUpdate(
                status=self.state.status,
                current_step=self.state.current_step,
                context=self.state.context,
                error=self.state.error,
            )
            await self._state_repo.upsert_state(
                saga_id=self.saga_id,
                saga_type=self.state.saga_type,
                update_data=update_data,
            )
        except Exception as e:
            logger.error("Saga %s: failed to save state: %s", self.saga_id, e)
            raise

    def get_state(self) -> SagaState:
        return self.state
