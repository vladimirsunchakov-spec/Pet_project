from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Any, Dict, Callable, Awaitable
from datetime import datetime
from pydantic import BaseModel

class SagaStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    FAILED = "failed"
    COMPENSATED = "compensated"
    COMPENSATION_FAILED = "compensation_failed"

class SagaStepStatus(Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    COMPENSATED = "compensated"

@dataclass
class SagaStep:
    id: int
    name: str
    action: Callable[[], Awaitable[Any]]
    compensation: Optional[Callable[[], Awaitable[None]]] = None
    status: SagaStepStatus = SagaStepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None

@dataclass
class SagaState:
    saga_id: str
    saga_type: str
    status: SagaStatus = SagaStatus.PENDING
    current_step: int = 0
    steps: list[SagaStep] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3

class SagaResult(BaseModel):
    saga_id: str
    status: str
    context: Dict[str, Any] = {}
    error: Optional[str] = None
    completed_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "saga_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "context": {"author_id": "550e8400-e29b-41d4-a716-446655440000"},
                "error": None,
                "competed_at": "2024-01-01T10:00:00"
            }
        }

class SagaStepResult(BaseModel):
    step_id: int
    name: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None

class SagaInfo(BaseModel):
    saga_id: str
    saga_type: str
    status: str
    current_step: int
    total_steps: int
    created_at: str
    updated_at: str
    is_active: bool
    error: Optional[str] = None

class SaraCreateRequest(BaseModel):
    saga_type: str
    data: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "saga_type": "create_author",
                "data": {
                    "name": "John Doe",
                    "rating": 4.5
                }
            }
        }