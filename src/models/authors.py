from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID, uuid4
from typing import TYPE_CHECKING, List
import sqlalchemy as sa
from sqlalchemy import Column, Boolean
from datetime import date, datetime

if TYPE_CHECKING:
    from .books import BookModel

class AuthorModel(Base):
    __tablename__ = "authors"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(sa.String())
    birth_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    country: Mapped[str | None] = mapped_column(sa.String(), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime, nullable=True)

    books: Mapped[List["BookModel"]] = relationship(
        secondary="author_book",
        back_populates="authors",
        )

