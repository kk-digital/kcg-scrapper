from os import path

from sqlalchemy import create_engine, Engine
from src.db.model.base import Base

import settings

_engine = None


def get_engine() -> Engine:
    global _engine

    if isinstance(_engine, Engine):
        return _engine

    db_location = path.join(settings.OUTPUT_FOLDER, settings.SQLITE_NAME)
    _engine = create_engine(f"sqlite+pysqlite:///{db_location}")

    return _engine


def emit_ddl(engine: Engine) -> None:
    Base.metadata.create_all(engine)
