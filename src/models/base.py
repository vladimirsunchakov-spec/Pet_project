import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeMeta, declarative_base, Mapped, mapped_column
from datetime import datetime, timezone

metadata = sa.MetaData()


class BaseServiceModel:
    created_At: Mapped[datetime] = mapped_column(
        sa.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_At: Mapped[datetime] = mapped_column(
        sa.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    is_Deleted: Mapped[bool] = mapped_column(sa.Boolean, default=False)


    @classmethod
    def on_conflict_constraint(cls) -> tuple | None:
        return None


Base: DeclarativeMeta = declarative_base(metadata=metadata, cls=BaseServiceModel)