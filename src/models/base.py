import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeMeta, declarative_base, Mapped, mapped_column
from datetime import datetime, timezone

metadata = sa.MetaData()


class BaseServiceModel:
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime,
        default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime,
        onupdate=datetime.now(timezone.utc)
    )
    is_deleted: Mapped[bool] = mapped_column(sa.Boolean, default=False)


    @classmethod
    def on_conflict_constraint(cls) -> tuple | None:
        return None


Base: DeclarativeMeta = declarative_base(metadata=metadata, cls=BaseServiceModel)