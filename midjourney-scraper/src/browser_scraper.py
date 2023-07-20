import csv
import logging
import random
from os import path
from typing import Optional

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
        self._viewport_sizes = settings.VIEWPORT_SIZES
        self._proxy_list_path = settings.PROXY_LIST
        self._storage_state_path = settings.STORAGE_STATE_PATH
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None

    def start_scraping(self) -> None:
        self._logger.info("Starting browser.")
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.firefox.launch(headless=self._headless)

    def _get_proxy(self) -> Optional[dict]:
        if not self._proxy_list_path:
            return

        with open(self._proxy_list_path, "r", newline="", encoding="utf-8") as fp:
            proxy_list = list(csv.DictReader(fp))

        proxy = proxy_list.pop(0)
        proxy_list.append(proxy)

        with open(self._proxy_list_path, "w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=proxy.keys())
            writer.writeheader()
            writer.writerows(proxy_list)

        return proxy

    def init_context(
        self, base_url: Optional[str], use_storage_state: bool
    ) -> BrowserContext:
        width, height = random.choice(self._viewport_sizes)
        viewport = {"width": width, "height": height}
        proxy = self._get_proxy()
        storage_state = (
            self._storage_state_path
            if use_storage_state and path.isfile(self._storage_state_path)
            else None
        )

        self._logger.info(
            f"Configuration: viewport: {viewport}, proxy: {proxy}, storage state: {use_storage_state}."
        )

        context = self._browser.new_context(
            base_url=base_url,
            viewport=viewport,
            proxy=proxy,
            storage_state=storage_state,
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        self._logger.debug("Browser context configured.")

        return context

    def close(self, context: BrowserContext) -> None:
        context.close()
        self._browser.close()
        self._playwright.stop()
        self._logger.debug("Browser closed.")
