from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Any, Dict, Callable, Awaitable
from datetime import datetime

class SagaStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    FAILED = "failed"
    COMPENSATED = "compensated"


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