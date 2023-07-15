import logging
from typing import Optional

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

    def start_scraping(
        self, prompt_filter: Optional[str], use_storage_state: bool
    ) -> None:
        self._logger.info("Starting scraper.")
        browser_scraper = BrowserScraper()
        context = None
        try:
            # init browser
            browser_scraper.start_scraping()
            context = browser_scraper.init_context(
                base_url=self._url, use_storage_state=use_storage_state
            )
            page = context.new_page()
            # start showcase stage
            showcase_scraper = ShowcaseScraper(page)
            showcase_scraper.start_scraping(
                prompt_filter=prompt_filter,
                use_storage_state=use_storage_state,
                browser_context=context,
            )
            # start download stage
            ImageDownloader(page).start_scraping()
            # todo check why not working on container
            # showcase_scraper.log_out(page)
            self._logger.info("End of operations.")
        finally:
            browser_scraper.close(context)
