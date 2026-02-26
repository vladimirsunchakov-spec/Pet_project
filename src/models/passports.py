from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from uuid import UUID, uuid4
from typing import TYPE_CHECKING
import sqlalchemy as sa

if TYPE_CHECKING:
    from .users import UserModel


class PassportModel(Base):
    __tablename__ = "passports"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    passport_number: Mapped[str] = mapped_column(sa.String(), unique=True, index=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True )

    # Связь с User (один к одному)
    user: Mapped["UserModel"] = relationship(back_populates="passport")