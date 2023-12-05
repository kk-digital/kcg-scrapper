import re
import urllib.parse

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

    async def _extract_urls(self):
        html = await self._page.content()
        soup = BeautifulSoup(html, "lxml")

        for pin in soup.find_all("a", href=re.compile(r"\/pin\/\d+\/")):
            self._pin_urls.add(urllib.parse.urljoin(self._page.url, pin["href"]))

    async def start_view(self):
        await _utils.scroll_to_bottom_while_do(
            page=self._page,
            scroll_delay=self._scroll_delay,
            check_bottom_times=self._check_bottom_times,
            do=self._extract_urls,
            stop_on_more_heading=True,
        )

    def get_pin_urls(self):
        return self._pin_urls
