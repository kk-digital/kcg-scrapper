import re
from typing import Callable

from bs4 import BeautifulSoup
from playwright.async_api import Page
from scrapy.settings import Settings

from scraper.views import _utils


class PinGridView:
    def __init__(self, page: Page, settings: Settings) -> None:
        self._page = page
        self._pin_urls = set()
        self._scroll_delay = settings["SCROLL_DELAY"]
        self._check_bottom_times = settings["CHECK_BOTTOM_TIMES"]
        self._short_wait = settings["SHORT_WAIT"]

    async def _scroll_to_bottom_while_do(self, do: Callable):
        await _utils.scroll_to_bottom_while_do(
            page=self._page,
            scroll_delay=self._scroll_delay,
            check_bottom_times=self._check_bottom_times,
            do=do,
            stop_on_more_heading=True,
        )

    async def _extract_pin_urls(self):
        html = await self._page.content()
        soup = BeautifulSoup(html, "lxml")
        for pin in soup.find_all("a", href=re.compile(r"\/pin\/\d+\/")):
            self._pin_urls.add(pin["href"])

    async def _scrape_sections(self):
        section_selector = ".Uxw"
        sections_number = await self._page.locator(section_selector).count()

        for i in range(sections_number):
            await self._page.locator(section_selector).nth(i).click()
            await self._page.wait_for_timeout(self._short_wait)
            await self._scroll_to_bottom_while_do(self._extract_pin_urls)
            await self._page.go_back()
            await self._page.wait_for_timeout(self._short_wait)

    async def start_view(self):
        await self._page.wait_for_timeout(self._short_wait)
        await self._scrape_sections()
        await self._scroll_to_bottom_while_do(self._extract_pin_urls)

    def get_pin_urls(self):
        return self._pin_urls
