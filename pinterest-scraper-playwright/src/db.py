from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from settings import SQLITE_DB_PATH


class Base(DeclarativeBase):
    pass


class Url(Base):
    __tablename__ = "url"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str]


engine = create_engine(f"sqlite:///{SQLITE_DB_PATH}")

Base.metadata.create_all(engine)
