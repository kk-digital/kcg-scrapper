import logging
import os
from typing import List

from playwright.sync_api import sync_playwright, BrowserContext, Page, Browser

import settings


class BrowserScraper:
    def __init__(self) -> None:
        self.logger = logging.getLogger(f"scraper.{__name__}")
        self.url = "https://www.midjourney.com"

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

    def _get_generations(self, page: Page) -> List[dict]:
        # generations = set()
        # page.goto(
        #     self.url_with_scheme + '/api/app/recent-jobs/?amount=45&dedupe=true&jobStatus=completed&jobType=upscale&orderBy=new&')
        # body_content = page.locator('body').text_content()
        # print(len(json.loads(body_content)))
        pass

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
                self._get_generations(page)
                self._log_out(page)
                self.logger.info("End of operations.")
            finally:
                context.close()
                browser.close()
                self.logger.debug("Browser and context closed.")
