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
            context=model.context if model.context is not None else {},
            error=model.error,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    @staticmethod
    def to_dict(model: SagaStateModel) -> dict:
        return {
            "saga_id": model.saga_id,
            "saga_type": model.saga_type,
            "status": model.status,
            "current_step": model.current_step,
            "context": model.context if model.context is not None else {},
            "error": model.error,
            "created_at": model.created_at.isoformat(),
            "updated_at": model.updated_at.isoformat(),
            "steps": [],
        }
