from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from uuid import UUID
from src.models.base import Base

class AuthorBio(Base):
    __tablename__ = 'author_bio'

    author_id: Mapped[UUID] = mapped_column(unique=True, index=True, nullable=False)
    rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    awards_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    biography: Mapped[str | None] = mapped_column(String, nullable=True)