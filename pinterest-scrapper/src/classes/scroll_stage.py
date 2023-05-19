import logging
import math
import time
from typing import Callable

from selenium.common import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver import ActionChains

import settings
from src.classes.base_stage import BaseStage

logger = logging.getLogger(f"scraper.{__name__}")


class ScrollStage(BaseStage):
    def __get_correct_val(self, val):
        return 0 if val is None else val

    def __get_scroll_height(self) -> int:
        scroll_height = self._driver.execute_script("return document.body.scrollHeight")
        return self.__get_correct_val(scroll_height)

    def __get_scroll_y(self) -> int:
        scroll_y = self._driver.execute_script("return window.scrollY")
        return self.__get_correct_val(scroll_y)

    def _scroll_and_scrape(self, fn: Callable, check_more_like_this=False) -> None:
        logger.debug("Starting to scroll.")
        # old_body_height = self.get_scroll_height()
        inner_height = self._driver.execute_script("return window.innerHeight")
        scroll_amount = int(inner_height * 0.2)
        seconds_sleep = 0
        while True:
            # exec fn in every scroll step
            try:
                fn()
            except (StaleElementReferenceException, NoSuchElementException) as e:
                # temporarily commented due to getting many logs
                # logger.debug(
                #     f"Error {e.__class__.__name__} accessing element, retrying..."
                # )
                pass

            # scroll 20% of viewport height since dom is dynamically populated,
            # removing els not in viewport and adding new ones
            ActionChains(self._driver).scroll_by_amount(0, scroll_amount).perform()
            # a short delay that also gives chance to load more els
            time.sleep(settings.SCROLL_DELAY)
            seconds_sleep += settings.SCROLL_DELAY

            new_body_height = self.__get_scroll_height()
            scroll_y = self.__get_scroll_y()
            # round up due to precision loss
            end_of_page = math.ceil(inner_height + scroll_y) >= new_body_height
            if end_of_page and seconds_sleep >= settings.TIMEOUT:
                logger.debug("End of page reached.")
                break

            if not end_of_page:
                seconds_sleep = 0

            if not check_more_like_this:
                continue

            # check if more like this el enters viewport
            el_top = self._driver.execute_script(
                """
            const el = document.querySelector("h2.GTB");
            if (!el) {
                return null
            }
            const elTop = el.getBoundingClientRect().top;
            return elTop;
            """
            )
            if el_top is None:
                continue

            is_in_viewport = el_top - inner_height <= 0
            if is_in_viewport:
                break
