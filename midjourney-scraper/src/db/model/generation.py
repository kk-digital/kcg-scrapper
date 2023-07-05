from sqlalchemy.orm import Mapped, mapped_column

from src.db.model.base import Base


class Generation(Base):
    __tablename__ = "generation"

    id: Mapped[int] = mapped_column(primary_key=True)
    generation_id: Mapped[str] = mapped_column(unique=True)
    generation_urls: Mapped[str]  # json serialized list of urls
    data: Mapped[str]
