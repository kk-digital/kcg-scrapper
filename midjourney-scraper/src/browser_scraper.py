import logging
import random
from typing import Optional

from playwright.sync_api import (
    sync_playwright,
    BrowserContext,
    Page,
    Browser,
    Playwright,
)

import settings
from fake_useragent import FakeUserAgent


class BrowserScraper:
    def __init__(self) -> None:
        self._logger = logging.getLogger(f"scraper.{__name__}")
        self._headless = not settings.HEADED
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._ua_browsers = settings.USER_AGENT_BROWSERS
        self._viewport_sizes = settings.VIEWPORT_SIZES

    def start_scraping(self) -> None:
        self._logger.info("Starting browser.")
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.firefox.launch(headless=self._headless)

    def init_context(self, base_url: Optional[str]) -> None:
        ua = FakeUserAgent(browsers=self._ua_browsers).random
        width, height = random.choice(self._viewport_sizes)
        viewport = {"width": width, "height": height}

        self._context = self._browser.new_context(
            base_url=base_url, user_agent=ua, viewport=viewport
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
