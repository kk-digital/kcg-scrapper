import csv
import json
import logging
import random
from typing import Optional, List

from playwright.sync_api import (
    sync_playwright,
    BrowserContext,
    Page,
    Browser,
    Playwright,
)

import settings


class BrowserScraper:
    def __init__(self) -> None:
        self._logger = logging.getLogger(f"scraper.{__name__}")
        self._headless = not settings.HEADED
        self._user_agent_list = settings.USER_AGENT_LIST
        self._viewport_sizes = settings.VIEWPORT_SIZES
        self._proxy_list_path = settings.PROXY_LIST
        self._ua_list_path = settings.USER_AGENT_LIST
        self._proxy_list: Optional[List[dict]] = None
        self._ua_list: Optional[List[dict]] = None
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._load_lists()

    def _load_lists(self) -> None:
        if self._proxy_list_path:
            with open(self._proxy_list_path, "r", encoding="utf-8", newline="") as fp:
                self._proxy_list = list(csv.DictReader(fp))

        if self._ua_list_path:
            with open(self._ua_list_path, "r", encoding="utf-8") as fp:
                self._ua_list = json.load(fp)

    def start_scraping(self) -> None:
        self._logger.info("Starting browser.")
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.firefox.launch(headless=self._headless)

    def init_context(self, base_url: Optional[str]) -> None:
        ua = random.choice(self._ua_list)["ua"]
        width, height = random.choice(self._viewport_sizes)
        viewport = {"width": width, "height": height}
        proxy = self._proxy_list_path and random.choice(self._proxy_list)
        self._logger.info(
            f"Configuration: UA: {ua}, viewport: {viewport}, proxy: {proxy}."
        )

        self._context = self._browser.new_context(
            base_url=base_url, user_agent=ua, viewport=viewport, proxy=proxy
        )
        self._context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        self._logger.debug("Browser context configured.")

    def get_page(self) -> Page:
        return self._context.new_page()

    def close(self) -> None:
        self._context.close()
        self._browser.close()
        self._playwright.stop()
        self._logger.debug("Browser closed.")
