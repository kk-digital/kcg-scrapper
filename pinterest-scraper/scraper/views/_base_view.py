from typing import Callable

from playwright.async_api import Page
from scrapy.settings import Settings

from scraper.views import _utils


class BaseView:
    def __init__(
        self, page: Page, settings: Settings, close_context: bool = False
    ) -> None:
        self._page = page
        self._close_context = close_context
        self._scroll_delay = settings["SCROLL_DELAY"]
        self._check_bottom_times = settings["CHECK_BOTTOM_TIMES"]
        self._short_wait = settings["SHORT_WAIT"]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        await self._page.close()
        if self._close_context:
            await self._page.context.close()

        return None

    async def _scroll_to_bottom_while_do(self, do: Callable):
        await _utils.scroll_to_bottom_while_do(
            page=self._page,
            scroll_delay=self._scroll_delay,
            check_bottom_times=self._check_bottom_times,
            do=do,
            stop_on_more_heading=True,
        )
