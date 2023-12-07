import itertools
import urllib.parse
from typing import Iterable

import scrapy
from playwright.async_api import Page
from scrapy.http import Request, Response

from scraper import utils
from scraper.views.board_grid import BoardGridView
from scraper.views.pin_grid import PinGridView


class PinsSpider(scrapy.Spider):
    name = "pins"
    allowed_domains = ["www.pinterest.com"]
    context_count = 0

    def start_requests(self) -> Iterable[Request]:
        self.proxy_list_cycle = itertools.cycle(utils.load_proxies())

        base_url = "https://www.pinterest.com/search/boards/?q={}&rs=typed"
        query = getattr(self, "query", None)
        if query is None:
            raise Exception("Must provide query.")

        query = urllib.parse.quote_plus(query)
        url = base_url.format(query)

        yield Request(
            url=url,
            meta=self.get_playwright_request_meta(),
            callback=self.extract_board_urls,
            errback=self.errback_close_page,
        )

    async def init_page(self, page, request):
        await page.add_init_script(
            script="Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

    def get_playwright_request_meta(self, new_context: bool = False):
        meta = {
            "playwright": True,
            "playwright_include_page": True,
            "playwright_page_init_callback": self.init_page,
        }

        if new_context:
            meta["playwright_context"] = "pinterest-context-" + str(self.context_count)
            self.context_count += 1
            proxy = next(self.proxy_list_cycle)
            meta["playwright_context_kwargs"] = {
                "proxy": {
                    "server": proxy["server"],
                    "username": proxy["username"],
                    "password": proxy["password"],
                }
            }

        return meta

    async def errback_close_page(self, failure, close_context: bool = False):
        page = failure.request.meta["playwright_page"]
        await page.close()
        if close_context:
            await page.context.close()

    async def extract_board_urls(self, response: Response):
        page: Page = response.meta["playwright_page"]

        view = BoardGridView(page, self.settings)
        await view.start_view()
        board_urls = view.get_board_urls()
        await page.close()

        for url in board_urls:
            meta = self.get_playwright_request_meta(new_context=True)
            yield response.follow(
                url,
                meta=meta,
                callback=self.extract_pin_urls,
                errback=lambda failure: self.errback_close_page(
                    failure, close_context=True
                ),
            )

    async def extract_pin_urls(self, response: Response):
        page: Page = response.meta["playwright_page"]

        view = PinGridView(page, self.settings)
        await view.start_view()
        pin_urls = view.get_pin_urls()
        await page.close()
        await page.context.close()

        print(pin_urls)
