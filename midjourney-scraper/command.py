import logging
import os

if os.getenv("PYTHON_ENV", "development") == "development":
    from dotenv import load_dotenv

    load_dotenv()

from src import logging_
from src.scraper import Scraper
from src.db import engine as db_engine


class Command:
    def __init__(self):
        logging_.configure()
        self._logger = logging.getLogger(f"scraper.{__name__}")
        engine = db_engine.get_engine()
        db_engine.emit_ddl(engine)
        self._session = db_engine.get_session(engine)

    def start_scraping(self) -> None:
        Scraper().start_scraping()

    def _close(self) -> None:
        self._session.close()


cli = Command()
try:
    cli.start_scraping()
finally:
    # noinspection PyProtectedMember
    cli._close()
