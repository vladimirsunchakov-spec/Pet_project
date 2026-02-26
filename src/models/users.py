from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID, uuid4
from typing import TYPE_CHECKING
import sqlalchemy as sa

if TYPE_CHECKING:
    from .passports import PassportModel

class UserModel(Base):
    __tablename__ = 'users'
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(sa.String(), unique=True, index=True)
    phone: Mapped[str] = mapped_column(sa.String(), unique=True, index=True)

# Связываем с паспортом (один к одному)
    passport: Mapped["PassportModel"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete")