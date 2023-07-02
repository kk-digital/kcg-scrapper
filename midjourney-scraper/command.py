import os

if os.getenv("PYTHON_ENV", "development") == "development":
    from dotenv import load_dotenv

    load_dotenv()

from src import logging_
from src.scraper import start_scraping

logging_.configure()

start_scraping()
