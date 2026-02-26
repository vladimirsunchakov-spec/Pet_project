from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID, uuid4
from typing import TYPE_CHECKING
import sqlalchemy as sa

if TYPE_CHECKING:
    from .authors import AuthorModel


class BookModel(Base):
    __tablename__ = "books"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(sa.String(), index=True)

    # Связь многие ко многим с Author через author_book
    authors: Mapped[list["AuthorModel"]] = relationship(
        secondary="author_book",
        back_populates="books")