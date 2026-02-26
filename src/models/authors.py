from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID, uuid4
from typing import TYPE_CHECKING
import sqlalchemy as sa

if TYPE_CHECKING:
    from .books import BookModel


class AuthorModel(Base):
    __tablename__ = "authors"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(sa.String(), index=True)

    # Связь многие ко многим с Book через author_book
    books: Mapped[list["BookModel"]] = relationship(
        secondary="author_book",
        back_populates="authors",
        cascade="all, delete")