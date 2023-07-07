import logging

from src.browser_scraper import BrowserScraper
from src.showcase_scraper import ShowcaseScraper


class Scraper:
    def __init__(self) -> None:
        self._logger = logging.getLogger(f"scraper.{__name__}")

    def start_scraping(self) -> None:
        self._logger.info("Starting scraper.")
        browser_scraper = BrowserScraper()
        browser_scraper.start_scraping()
        try:
            ShowcaseScraper(browser_scraper).start_scraping()
        finally:
            browser_scraper.close()
