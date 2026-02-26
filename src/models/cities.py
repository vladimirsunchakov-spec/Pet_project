from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from uuid import UUID, uuid4
from typing import TYPE_CHECKING
import sqlalchemy as sa

if TYPE_CHECKING:
    from .countries import CountryModel


class CityModel(Base):
    __tablename__ = "cities"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(sa.String(), index=True)
    country_id: Mapped[UUID] = mapped_column(
        ForeignKey("countries.id", ondelete="CASCADE"),
        index=True
    )

    # Связь с Country
    country: Mapped["CountryModel"] = relationship(back_populates="cities")