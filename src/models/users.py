from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID, uuid4
from typing import TYPE_CHECKING
import sqlalchemy as sa

if TYPE_CHECKING:
    from .passports import PassportModel
    from src.schemas.users import UserCreate

class UserModel(Base):
    __tablename__ = 'users'
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(sa.String(), unique=True)
    phone: Mapped[str] = mapped_column(sa.String(), unique=True)

    passport: Mapped["PassportModel"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete")

    @classmethod
    def from_schema(cls, data: "UserCreate") -> "UserModel":
        return cls(
            username=data.username,
            phone=data.phone)

    def update_from_schema(self, data: "UserCreate") -> None:
        if data.username is not None:
            self.username = data.username
        if data.phone is not None:
            self.phone = data.phone