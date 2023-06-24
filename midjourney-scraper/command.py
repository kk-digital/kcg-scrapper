from src import logging_
from src.scraper import Scraper

logging_.configure()

Scraper().start_scraping()
