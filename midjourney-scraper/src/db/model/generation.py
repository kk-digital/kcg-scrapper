from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from src.db.model.base import Base


class Generation(Base):
    __tablename__ = "generation"

    id: Mapped[int] = mapped_column(primary_key=True)
    generation_id: Mapped[str] = mapped_column(unique=True)
    generation_urls: Mapped[List["GenerationUrl"]] = relationship(
        back_populates="generation", cascade="all, delete-orphan"
    )
    data: Mapped[str]
    status: Mapped[str]  # pending (default), completed or failed


class GenerationUrl(Base):
    __tablename__ = "generation_url"

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[str]
    generation_id: Mapped[int] = mapped_column(ForeignKey("generation.id"))
    generation: Mapped[Generation] = relationship(back_populates="generation_urls")
