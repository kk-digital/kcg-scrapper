from os import path

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session

from src.db.model import Base

import settings

_engine = None
_session = None


def get_engine() -> Engine:
    global _engine

    if isinstance(_engine, Engine):
        return _engine

    db_location = path.join(settings.OUTPUT_FOLDER, settings.SQLITE_NAME)
    _engine = create_engine(f"sqlite+pysqlite:///{db_location}")

    return _engine


def emit_ddl(engine: Engine) -> None:
    Base.metadata.create_all(engine)


def get_new_session(engine: Engine) -> Session:
    return Session(engine)


def get_session(engine: Engine) -> Session:
    global _session

    if isinstance(_session, Session):
        return _session

    _session = get_new_session(engine)

    return _session
