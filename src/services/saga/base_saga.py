from typing import Optional, Any, Dict, Callable, Awaitable
from uuid import UUID, uuid4
import logging
from datetime import datetime
from src.schemas.saga import SagaStatus, SagaStep, SagaState, SagaStepStatus

logger = logging.getLogger(__name__)

class BaseSaga:
    def __init__(self, saga_id: Optional[str] = None):
        self.saga_id = saga_id or str(uuid4())
        self.state = SagaState(
            saga_id=self.saga_id,
            saga_type=self.__class__.__name__
        )
        self._steps: list[SagaStep] = []
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

    async def execute(self) -> Dict[str, Any]:
        self.state.status = SagaStatus.IN_PROGRESS
        await self._save_state()

        try:
            for idx, step in enumerate(self._steps):
                self._current_step_index = idx
                self.state.current_step = idx

                logger.info(f"Saga {self.saga_id}: Executing step {idx + 1}/{len(self._steps)} - {step.name}")

                step.status = SagaStepStatus.EXECUTING
                await self._save_state()

                try:
                    result = await step.action()
                    step.status = SagaStepStatus.SUCCESS
                    step.result = result
                    logger.info(f"Saga {self.saga_id}: Step {step.name} completed successfully")
                except Exception as e:
                    step.status = SagaStepStatus.FAILED
                    step.error = str(e)
                    logger.error(f"Saga {self.saga_id}: Step {step.name} failed {e}")
                    await self._compensate(idx)
                    raise

            self.state.status = SagaStatus.COMPLETED
            await self._save_state()

            logger.info(f"Saga {self.saga_id}: Completed successfully")
            return {
                "saga_id": self.saga_id,
                "status": "completed",
                "context": self.state.context
            }

        except Exception as e:
            self.state.status = SagaStatus.FAILED
            self.state.error = str(e)
            await self._save_state()
            raise

    async def _compensate(self, failed_step_index: int):
        self.state.status = SagaStatus.COMPENSATING
        logger.info(f"Saga {self.saga_id}: Starting compensation form step {failed_step_index}")

        for idx in range(failed_step_index -1, -1, -1):
            step = self._steps[idx]
            if step.status == SagaStepStatus.SUCCESS and step.compensation:
                try:
                    logger.info(f"Saga {self.saga_id}: Compensating step {idx + 1} - {step.name}")
                    await step.compensation()
                    step.status = SagaStepStatus.COMPENSATED
                except Exception as e:
                    logger.error(f"Saga {self.saga_id}: Compensation failed for step {step.name}: {e}")

                    self.state.error = f"Compensation failed for step {step.name}: {e}"
                    break

        self.state.status = SagaStatus.COMPENSATED
        await self._save_state()
        logger.info(f"Saga {self.saga_id}: Compensation completed")

    async def _save_state(self):
        self.state.updated_at = datetime.now()
        logger.debug(f"Saga {self.saga_id}: Saving state - {self.state.status}")
        pass

    def get_state(self) ->SagaState:
        return self.state

