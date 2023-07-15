import json
import logging
import os
from os import path
from typing import Optional

from playwright.sync_api import Page, Request, BrowserContext
from sqlalchemy import select

from src.db import engine as db_engine

import settings
from src.db.model import Generation, GenerationUrl


class ShowcaseScraper:
    def __init__(self, page: Page) -> None:
        engine = db_engine.get_engine()
        self._session = db_engine.get_session(engine)
        self._logger = logging.getLogger(f"scraper.{__name__}")
        self._target_endpoint = "/api/app/recent-jobs/"
        self._page = page
        self._storage_state_path = settings.STORAGE_STATE_PATH

    def _log_in(
        self, page: Page, use_storage_state: bool, browser_context: BrowserContext
    ) -> None:
        storage_state_exists = path.isfile(self._storage_state_path)
        execute_login = not use_storage_state or not storage_state_exists
        if execute_login:
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

        # save or renew storage state
        if use_storage_state:
            browser_context.storage_state(path=self._storage_state_path)
        self._logger.debug("Logged in.")

    def _insert_generation(self, generation: dict):
        # first check for duplicate generation
        generation_id = generation["id"]
        stmt = select(Generation).filter_by(generation_id=generation_id)
        found = self._session.scalar(stmt)
        if found:
            return

        json_data = json.dumps(generation)
        generation_urls = [
            GenerationUrl(value=url) for url in generation["image_paths"]
        ]
        new_generation = Generation(
            generation_id=generation_id,
            generation_urls=generation_urls,
            data=json_data,
            status="pending",
        )
        self._session.add(new_generation)

    def _request_handler(self, request: Request, prompt_filter: Optional[str]) -> None:
        if not self._target_endpoint in request.url:
            return

        data = request.response().json()
        self._logger.info(f"Got {len(data)} new generations.")
        for generation in data:
            if generation["prompt"] is None:
                continue
            if prompt_filter:
                passed_filter = prompt_filter.lower() in generation["prompt"].lower()
                if not passed_filter:
                    continue

            self._insert_generation(generation)

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

    def start_scraping(
        self,
        prompt_filter: Optional[str],
        use_storage_state: bool,
        browser_context: BrowserContext,
    ) -> None:
        self._logger.info("Starting showcase scraper.")
        self._page.goto("/")
        self._log_in(
            self._page,
            use_storage_state=use_storage_state,
            browser_context=browser_context,
        )
        self._page.on(
            "requestfinished",
            lambda request: self._request_handler(request, prompt_filter),
        )
        self._page.goto("/app/feed/?sort=new")
        self._page.get_by_role("button", name="Grids").click()
        self._page.wait_for_timeout(3000)  # let ui respond
        self._scroll_generations(self._page)
        self._logger.info("End of showcase stage.")

    def log_out(self, page: Page) -> None:
        page.goto("/")
        page.get_by_role("button", name="Account").click()
        page.get_by_role("menuitem", name="Sign Out").click()
        page.wait_for_url("/home*")
        self._logger.debug("Logged out.")
