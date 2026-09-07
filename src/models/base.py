import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, declarative_base, Mapped, mapped_column, DeclarativeBase
from datetime import datetime, timezone
from typing import Optional

class Base(DeclarativeBase):

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True),
        onupdate=datetime.now(timezone.utc),
        nullable=True,
    )
    is_deleted: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)

    @classmethod
    def on_conflict_constraint(cls) -> tuple | None:
        return None
