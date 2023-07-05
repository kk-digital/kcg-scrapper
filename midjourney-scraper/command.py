import os

if os.getenv("PYTHON_ENV", "development") == "development":
    from dotenv import load_dotenv

    load_dotenv()

from src import logging_
from src.scraper import start_scraping
from src.db import engine as db_engine

engine = db_engine.get_engine()
db_engine.emit_ddl(engine)

logging_.configure()

start_scraping()
