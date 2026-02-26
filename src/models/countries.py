from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID, uuid4
from typing import TYPE_CHECKING
import sqlalchemy as sa

if TYPE_CHECKING:
    from .cities import CityModel


class CountryModel(Base):
    __tablename__ = "countries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(sa.String(), index=True)
    continent: Mapped[str] = mapped_column(sa.String(), index=True)

    # Связь один ко многим с City
    cities: Mapped[list["CityModel"]] = relationship(
        back_populates="country",
        cascade="all, delete-orphan")