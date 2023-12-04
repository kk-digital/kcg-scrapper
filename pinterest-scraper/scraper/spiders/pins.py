import urllib.parse
from typing import Iterable

import scrapy
from playwright.async_api import Page
from scrapy.http import Request, Response

from scraper.views.board_grid import BoardGridView
from scraper.views.pin_grid import PinGridView


class PinsSpider(scrapy.Spider):
    name = "pins"
    allowed_domains = ["www.pinterest.com"]

    def start_requests(self) -> Iterable[Request]:
        base_url = "https://www.pinterest.com/search/boards/?q={}&rs=typed"
        query = getattr(self, "query", None)
        if query is None:
            raise Exception("Must provide query.")

        query = urllib.parse.quote_plus(query)
        url = base_url.format(query)

        yield Request(
            url=url,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_init_callback": self.init_page,
            },
            callback=self.extract_board_urls,
            errback=self.errback_close_page,
        )

    async def init_page(self, page, request):
        await page.add_init_script(
            script="Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

    async def errback_close_page(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()

    async def extract_board_urls(self, response: Response):
        page: Page = response.meta["playwright_page"]
        await page.wait_for_timeout(5000)  # TODO move to view

        view = BoardGridView(page, self.settings)
        await view.start_view()
        board_urls = view.get_board_urls()
        await page.close()

        for url in board_urls:
            yield response.follow(
                url,
                callback=self.extract_pin_urls,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_init_callback": self.init_page,
                },
                errback=self.errback_close_page,
            )

    async def extract_pin_urls(self, response: Response):
        page: Page = response.meta["playwright_page"]
        await page.wait_for_timeout(5000)

        view = PinGridView(page, self.settings)
        await view.start_view()
        pin_urls = view.get_pin_urls()
        await page.close()

        print(pin_urls)
