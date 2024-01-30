import asyncio
import logging
import math
import time
from typing import Callable

import psutil
from playwright.async_api import Page

logger = logging.getLogger(__name__)


async def scroll_to_bottom_while_do(
    page: Page,
    scroll_delay: int,
    check_bottom_times: int,
    do: Callable,
    stop_on_more_heading: bool = False,
):
    document_element_handle = await page.evaluate_handle("document.documentElement")
    client_height = await (
        await document_element_handle.get_property("clientHeight")
    ).json_value()
    scroll_amount = client_height * 0.2
    bottom_checks = 0
    amount_scrolled = client_height
    get_scrolled_from_api = False
    more_heading_locator = page.locator("h2.GTB")
    time_counter = time.perf_counter()

    while True:
        if time.perf_counter() - time_counter >= 10:
            logger.info("Checking memory usage")
            time_counter = time.perf_counter()
            mem_usage_percent = psutil.virtual_memory().percent
            logger.info(f"Memory usage is {mem_usage_percent}%")
            if mem_usage_percent > 95:
                logger.info(
                    f"Memory usage {mem_usage_percent}% exceeded threshold, stopping scroll"
                )
                break

        do_result = do()
        if asyncio.iscoroutine(do_result):
            await do_result

        await page.mouse.wheel(0, scroll_amount)

        if stop_on_more_heading and await more_heading_locator.is_visible():
            bounding_box = await more_heading_locator.bounding_box()
            more_heading_crossed_viewport = bounding_box["y"] - client_height <= 0
            if more_heading_crossed_viewport:
                break

        if get_scrolled_from_api:
            get_scrolled_from_api = False
            amount_scrolled = await (
                await document_element_handle.get_property("scrollTop")
            ).json_value()
            amount_scrolled += client_height
        else:
            amount_scrolled += scroll_amount

        await asyncio.sleep(scroll_delay)

        scroll_height = await (
            await document_element_handle.get_property("scrollHeight")
        ).json_value()
        bottom_reached = math.ceil(amount_scrolled) >= scroll_height

        if bottom_reached:
            get_scrolled_from_api = True
            bottom_checks += 1
            if bottom_checks >= check_bottom_times:
                break
        else:
            bottom_checks = 0
