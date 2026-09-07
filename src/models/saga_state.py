from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from src.models.base import Base
import uuid
from src.schemas.saga import SagaState, SagaStatus

class SagaStateModel(Base):
    __tablename__ = "saga_state"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    saga_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    saga_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    context: Mapped[dict] = mapped_column(JSON, default={})
    error: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    def to_state(self):
        return SagaState(
            saga_id=self.saga_id,
            saga_type=self.saga_type,
            status=SagaStatus(self.status),
            current_step=self.current_step,
            error=self.error,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

