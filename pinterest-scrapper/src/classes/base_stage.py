import logging
import threading
import time
from datetime import datetime
from sqlite3 import Row
from typing import Optional, Union

from selenium import webdriver

# just import to install driver
# noinspection PyUnresolvedReferences
import chromedriver_autoinstaller
from fake_useragent import UserAgent
from selenium.webdriver.support.wait import WebDriverWait

import settings
from src import db, utils

logger = logging.getLogger(f"scraper.{__name__}")
lock = threading.Lock()
stop_event = threading.Event()


class BaseStage:
    def __init__(
        self, job: Union[Row, dict], max_workers: int = None, headless: bool = True
    ) -> None:
        self._db = db
        self._job = job
        self._max_workers = max_workers
        self._driver: Optional[webdriver.Chrome] = None
        self._wait: Optional[WebDriverWait] = None
        self._headless = headless
        self.__last_proxy_rotation = None
        self._stop_event = stop_event

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
        # anti detection options
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        with lock:
            proxy = utils.get_next_proxy()
            if proxy:
                # load extension options does not work for uc
                options.add_argument(f"--load-extension={proxy}")
                self.__last_proxy_rotation = datetime.now()

            time.sleep(2)
            self._driver = webdriver.Chrome(options=options)
            self._driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

        self._driver.set_window_size(1280, 1024)
        self._driver.set_page_load_timeout(settings.TIMEOUT)
        self._wait = WebDriverWait(self._driver, settings.TIMEOUT)
        logger.debug("Driver set up.")

    def __check_proxy_rotation(self) -> None:
        if not self.__last_proxy_rotation:
            return

        delta = datetime.now() - self.__last_proxy_rotation
        delta_min = delta.total_seconds() / 60
        if delta_min >= settings.PROXY_ROTATE_MINUTES:
            self.close()
            self._driver = None
            self.__init_driver()

    def start_scraping(self) -> None:
        logger.debug("Starting scraping.")
        self.__init_driver()
        self.__check_proxy_rotation()

    def close(self) -> None:
        if not self._driver:
            return

        self._driver.quit()
        logger.debug("Driver closed.")
