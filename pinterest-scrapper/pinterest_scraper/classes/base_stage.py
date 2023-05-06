import logging
from datetime import datetime
from sqlite3 import Row
from typing import Optional

import undetected_chromedriver as webdriver
from fake_useragent import UserAgent
from selenium.webdriver.support.wait import WebDriverWait

import settings
from pinterest_scraper import db, utils
from settings import TIMEOUT, PROXY_ROTATE_MINUTES

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
        self.__get_next_proxy = None
        self.__last_proxy_rotation = None

    def __init_driver(self) -> None:
        # init driver if not already provided
        if isinstance(self._driver, webdriver.Chrome):
            return

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
        if self.__get_next_proxy:
            options.add_argument(f"--proxy-server=https://{self.__get_next_proxy()}")
            self.__last_proxy_rotation = datetime.now()

        self._driver = webdriver.Chrome(options=options)
        self._driver.set_window_size(1280, 1024)
        self._driver.set_page_load_timeout(TIMEOUT)
        self._wait = WebDriverWait(self._driver, TIMEOUT)
        logger.debug("Driver set up.")

    def __check_proxy_rotation(self) -> None:
        delta = datetime.now() - self.__last_proxy_rotation
        delta_min = delta.total_seconds() / 60
        if delta_min >= PROXY_ROTATE_MINUTES:
            self.close()
            self._driver = None
            self.__init_driver()

    def start_scraping(self) -> None:
        logger.debug("Starting scraping.")

        proxylist_path = settings.PROXY_LIST_PATH
        if proxylist_path:
            if not self.__get_next_proxy:
                self.__get_next_proxy = utils.init_proxy_list(proxylist_path)
            else:
                self.__check_proxy_rotation()

        self.__init_driver()

    def close(self) -> None:
        self._driver.quit()
        logger.debug("Driver closed.")
