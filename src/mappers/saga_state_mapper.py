from typing import Any
from src.models.saga_state import SagaStateModel
from src.schemas.saga import SagaState, SagaStatus


class SagaStateMapper:
    @staticmethod
    def to_state(model: SagaStateModel) -> SagaState:
        return SagaState(
            saga_id=model.saga_id,
            saga_type=model.saga_type,
            status=SagaStatus(model.status),
            current_step=model.current_step,
            context=model.context,
            error=model.error,
        )

    @staticmethod
    def to_dict(model: SagaStateModel) -> dict[str, Any]:
        return {
            "saga_id": model.saga_id,
            "saga_type": model.saga_type,
            "status": model.status,
            "current_step": model.current_step,
            "context": model.context,
            "error": model.error,
            "steps": [],
        }
