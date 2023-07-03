import logging
import os
from typing import List

from playwright.sync_api import sync_playwright, BrowserContext, Page, Browser, Request

import settings


class BrowserScraper:
    def __init__(self) -> None:
        self.logger = logging.getLogger(f"scraper.{__name__}")
        self.url = "https://www.midjourney.com"
        self._target_endpoint = "/api/app/recent-jobs/"

    def _init_context(self, browser: Browser) -> BrowserContext:
        context = browser.new_context(base_url=self.url)
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        self.logger.debug("Browser context configured.")

        return context

    def _log_in(self, page: Page) -> None:
        page.goto("/")
        page.get_by_role("button", name="Sign In").first.click()
        page.get_by_label("EMAIL OR PHONE NUMBER").type(
            os.environ["DS_EMAIL"], delay=settings.ACTIONS_DELAY
        )
        page.get_by_label("PASSWORD").type(
            os.environ["DS_PASSWORD"], delay=settings.ACTIONS_DELAY
        )
        page.get_by_role("button", name="Log In").click()
        page.get_by_role("button", name="Authorize").click()
        page.wait_for_url("/app*")
        self.logger.debug("Logged in.")

    def _request_handler(self, request: Request) -> None:
        if not self._target_endpoint in request.url:
            return

        data = request.response().json()
        self.logger.debug(f"Got {len(data)} new generations.")
        # todo logic to push data to db

    def _scroll_generations(self, page: Page) -> None:
        self.logger.info("Starting scrolling stage...")
        document_element = page.evaluate_handle("document.documentElement")
        get_scroll_height = lambda: document_element.get_property(
            "scrollHeight"
        ).json_value()
        last_scroll_height = get_scroll_height()

        for _ in range(settings.SCROLL_TIMES):
            page.evaluate(f"window.scrollTo(0, {last_scroll_height})")
            page.wait_for_timeout(settings.SCROLL_DELAY)
            last_scroll_height = get_scroll_height()

    def _log_out(self, page: Page) -> None:
        page.get_by_role("button", name="Account").click()
        page.get_by_role("menuitem", name="Sign Out").click()
        page.wait_for_url("/home*")
        self.logger.debug("Logged out.")

    def start_scraping(self) -> None:
        self.logger.info("Starting browser.")
        with sync_playwright() as playwright:
            browser = playwright.firefox.launch(headless=not settings.HEADED)
            context = self._init_context(browser)
            try:
                page = context.new_page()
                self._log_in(page)
                page.on("requestfinished", self._request_handler)
                page.goto("/app/feed/?sort=new")
                self._scroll_generations(page)
                self._log_out(page)
                self.logger.info("End of operations.")
            finally:
                context.close()
                browser.close()
                self.logger.debug("Browser and context closed.")
