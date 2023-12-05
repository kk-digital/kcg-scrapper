from bs4 import BeautifulSoup
from playwright.async_api import Page
from scrapy.settings import Settings

from scraper.views import _utils


class BoardGridView:
    def __init__(self, page: Page, settings: Settings) -> None:
        self._page = page
        self._board_urls = set()
        self._scroll_delay = settings["SCROLL_DELAY"]
        self._check_bottom_times = settings["CHECK_BOTTOM_TIMES"]
        self._short_wait = settings["SHORT_WAIT"]

    async def _extract_urls(self):
        html = await self._page.content()
        soup = BeautifulSoup(html, "lxml")

        for board in soup.select("[role=listitem] a"):
            self._board_urls.add(board["href"])

    async def start_view(self):
        await self._page.wait_for_timeout(self._short_wait)
        await _utils.scroll_to_bottom_while_do(
            page=self._page,
            scroll_delay=self._scroll_delay,
            check_bottom_times=self._check_bottom_times,
            do=self._extract_urls,
        )

    def get_board_urls(self):
        return self._board_urls
