import logging
from sqlite3 import Row
from typing import Optional

import undetected_chromedriver as webdriver
from fake_useragent import UserAgent
from selenium.webdriver.support.wait import WebDriverWait

from pinterest_scraper import db
from settings import TIMEOUT

logger = logging.getLogger(f"scraper.{__name__}")


class BaseStage:
    def __init__(
            self, job: Row | dict, max_workers: int = None, headless: bool = True
    ) -> None:
        self._db = db
        self._job = job
        self._max_workers = max_workers
        self._driver: Optional[webdriver.Chrome] = None
        self._wait: Optional[WebDriverWait] = None
        self._headless = headless

    def __init_driver(self) -> None:
        # init driver if not already provided
        if not isinstance(self._driver, webdriver.Chrome):
            ua = UserAgent(browsers=["chrome", "edge", "firefox", "safari", "opera"])
            ua = ua.random
            options = webdriver.ChromeOptions()
            if self._headless:
                options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-logging")
            options.add_argument("--log-level=3")
            options.add_argument(f"user-agent={ua}")
            options.add_argument("--blink-settings=imagesEnabled=false")
            options.add_argument("--disable-extensions")
            self._driver = webdriver.Chrome(options=options)
            self._driver.set_window_size(1280, 1024)
            self._driver.set_page_load_timeout(TIMEOUT)
            logger.debug("Driver set up.")

        self._wait = WebDriverWait(self._driver, TIMEOUT)

    def start_scraping(self) -> None:
        logger.debug("Starting scraping.")
        self.__init_driver()

    def close(self) -> None:
        self._driver.quit()
        logger.debug("Driver closed.")
