import logging

from src import logging_
from src.browser_scraper import BrowserScraper
from src.image_downloader import ImageDownloader
from src.showcase_scraper import ShowcaseScraper

from src.db import engine as db_engine


class Scraper:
    def __init__(self) -> None:
        self._logger = logging.getLogger(f"scraper.{__name__}")
        self._url = "https://www.midjourney.com"

    @staticmethod
    def init_config() -> None:
        logging_.configure()
        engine = db_engine.get_engine()
        db_engine.emit_ddl(engine)

    def start_scraping(self) -> None:
        self._logger.info("Starting scraper.")
        browser_scraper = BrowserScraper()
        try:
            # init browser
            browser_scraper.start_scraping()
            browser_scraper.init_context(base_url=self._url)
            page = browser_scraper.get_page()
            # start showcase stage
            showcase_scraper = ShowcaseScraper(page)
            showcase_scraper.start_scraping()
            # start download stage
            ImageDownloader(page).start_scraping()
            # todo check why not working on container
            # showcase_scraper.log_out(page)
        finally:
            browser_scraper.close()
