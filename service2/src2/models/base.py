from sqlalchemy.orm import DeclarativeMeta, Mapped, mapped_column, declarative_base
from datetime import datetime, timezone
import sqlalchemy as sa
from typing import Optional

metadata = sa.MetaData()

class BaseServiceModel():

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime,
        default=datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime,
        onupdate=datetime.now(timezone.utc),
    )
    is_deleted: Mapped[bool] = mapped_column(
        sa.Boolean, default=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime, nullable=True
    )

    @classmethod
    def on_conflict_constraint(cls) -> tuple | None:
        return None

Base: DeclarativeMeta = declarative_base(metadata=metadata, cls=BaseServiceModel)


