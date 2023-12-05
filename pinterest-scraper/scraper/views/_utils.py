import asyncio
import math
from typing import Callable

from playwright.async_api import Page


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

    while True:
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
