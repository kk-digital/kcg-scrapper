import logging

from src.browser_scraper import BrowserScraper


class Scraper:
    def __init__(self) -> None:
        self._logger = logging.getLogger(f"scraper.{__name__}")

    def start_scraping(self) -> None:
        self._logger.info("Starting scraper.")
        BrowserScraper().start_scraping()
