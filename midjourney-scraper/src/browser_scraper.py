import json
import logging
import os

from playwright.sync_api import sync_playwright, BrowserContext, Page, Browser, Request
from sqlalchemy import select

from src.db import engine as db_engine

import settings
from src.db.model import Generation, GenerationUrl


class BrowserScraper:
    def __init__(self) -> None:
        engine = db_engine.get_engine()
        self._session = db_engine.get_session(engine)
        self._logger = logging.getLogger(f"scraper.{__name__}")
        self.url = "https://www.midjourney.com"
        self._target_endpoint = "/api/app/recent-jobs/"

    def _init_context(self, browser: Browser) -> BrowserContext:
        context = browser.new_context(base_url=self.url)
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        self._logger.debug("Browser context configured.")

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
        self._logger.debug("Logged in.")

    def _request_handler(self, request: Request) -> None:
        if not self._target_endpoint in request.url:
            return

        data = request.response().json()
        self._logger.debug(f"Got {len(data)} new generations.")
        for generation in data:
            # first check for duplicate generation
            generation_id = generation["id"]
            stmt = select(Generation).filter_by(generation_id=generation_id)
            found = self._session.scalar(stmt)
            if found:
                continue

            json_data = json.dumps(generation)
            generation_urls = [
                GenerationUrl(value=url) for url in generation["image_paths"]
            ]
            new_generation = Generation(
                generation_id=generation_id,
                generation_urls=generation_urls,
                data=json_data,
            )
            self._session.add(new_generation)

        self._session.commit()

    def _scroll_generations(self, page: Page) -> None:
        self._logger.info("Starting scrolling stage...")
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
        self._logger.debug("Logged out.")

    def start_scraping(self) -> None:
        self._logger.info("Starting browser.")
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
                self._logger.info("End of operations.")
            finally:
                context.close()
                browser.close()
                self._logger.debug("Browser and context closed.")
