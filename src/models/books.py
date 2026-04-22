from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID, uuid4
from typing import TYPE_CHECKING, List
import sqlalchemy as sa

if TYPE_CHECKING:
    from .authors import AuthorModel
    from src.schemas.books import BookCreate

class BookModel(Base):
    __tablename__ = "books"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(sa.String())


    authors: Mapped[List["AuthorModel"]] = relationship(
        secondary="author_book",
        back_populates="books")

    @classmethod
    def from_schema(cls, data: "BookCreate") -> "BookModel":
        return cls(
            title=data.title)

    def update_from_schema(self, data: "BookUpdate") -> None:
        if data.title is not None:
            self.title = data.title