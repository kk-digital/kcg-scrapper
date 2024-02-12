import logging
import math
import time
from typing import Callable

import psutil
from playwright.sync_api import Page

logger = logging.getLogger(__name__)


def scroll_to_bottom_while_do(
    page: Page,
    scroll_delay: int | float,
    check_bottom_times: int,
    do: Callable,
    stop_on_more_heading: bool = False,
):
    document_element_handle = page.evaluate_handle("document.documentElement")
    client_height = document_element_handle.get_property("clientHeight").json_value()
    scroll_amount = client_height * 0.2
    bottom_checks = 0
    amount_scrolled = client_height
    get_scrolled_from_api = False
    more_heading_locator = page.locator("h2.GTB")
    time_counter = time.perf_counter()

    while True:
        logger.debug("Checking memory usage")
        mem_usage_percent = psutil.virtual_memory().percent
        swap_usage_percent = psutil.swap_memory().percent
        if (time.perf_counter() - time_counter) >= 30:
            time_counter = time.perf_counter()
            logger.info(
                f"Memory usage {mem_usage_percent}%, swap usage {swap_usage_percent}%"
            )
        if mem_usage_percent > 90 or swap_usage_percent > 70:
            logger.info(
                f"Memory usage exceeded threshold. ram {mem_usage_percent}% swap {swap_usage_percent}&, stopping scroll"
            )
            break

        do()
        page.mouse.wheel(0, scroll_amount)

        if stop_on_more_heading and more_heading_locator.is_visible():
            bounding_box = more_heading_locator.bounding_box()
            more_heading_crossed_viewport = bounding_box["y"] - client_height <= 0
            if more_heading_crossed_viewport:
                break

        if get_scrolled_from_api:
            get_scrolled_from_api = False
            amount_scrolled = document_element_handle.get_property(
                "scrollTop"
            ).json_value()
            amount_scrolled += client_height
        else:
            amount_scrolled += scroll_amount

        time.sleep(scroll_delay)

        scroll_height = document_element_handle.get_property(
            "scrollHeight"
        ).json_value()
        bottom_reached = math.ceil(amount_scrolled) >= scroll_height

        if bottom_reached:
            get_scrolled_from_api = True
            bottom_checks += 1
            if bottom_checks >= check_bottom_times:
                break
        else:
            bottom_checks = 0
