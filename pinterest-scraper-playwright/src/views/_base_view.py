from typing import Callable

from playwright.sync_api import Page

from src.settings import CHECK_BOTTOM_TIMES, SCROLL_DELAY, SHORT_WAIT
from src.views._utils import scroll_to_bottom_while_do


class BaseView:
    def __init__(self, page: Page) -> None:
        self._page = page
        self._scroll_delay = SCROLL_DELAY
        self._check_bottom_times = CHECK_BOTTOM_TIMES
        self._short_wait = SHORT_WAIT

    def _scroll_to_bottom_while_do(self, do: Callable):
        scroll_to_bottom_while_do(
            page=self._page,
            scroll_delay=self._scroll_delay,
            check_bottom_times=self._check_bottom_times,
            do=do,
            stop_on_more_heading=True,
        )
