import itertools
import json
import re
import urllib.parse
from json import JSONDecodeError
from typing import Iterable

import scrapy
from playwright._impl._errors import TargetClosedError
from playwright.async_api import Page
from scrapy.http import Request, Response, TextResponse

from scraper import utils
from scraper.views.board_grid import BoardGridView
from scraper.views.pin_grid import PinGridView


class PinsSpider(scrapy.Spider):
    name = "pins"
    allowed_domains = ["www.pinterest.com"]
    context_count = 0
    board_count = 0
    pin_count = 0
    scraped_boards_count = 0
    scraped_pins_count = 0

    def start_requests(self) -> Iterable[Request]:
        self.proxy_list_cycle = itertools.cycle(utils.load_proxies())
        self.context_names = set()

        base_url = "https://www.pinterest.com/search/boards/?q={}&rs=typed"
        query = getattr(self, "query", None)
        if query is None:
            raise Exception("Must provide query.")

        query = urllib.parse.quote_plus(query)
        url = base_url.format(query)
        self.logger.info(f'start_requests method. Query "{query}", initial url "{url}"')

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
            "proxy": None,
        }

        if new_context:
            context_name = "pinterest-context-" + str(self.context_count)
            if context_name in self.context_names:
                raise Exception("Duplicated context name")
            self.context_names.add(context_name)
            meta["playwright_context"] = context_name
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

    async def errback_close_page(self, failure):
        request = failure.request
        self.logger.info(f"There was a problem scraping {request.url}")
        self.logger.error(repr(failure))
        if failure.check(TargetClosedError):
            request.dont_filter = True
            yield request
        else:
            page = request.meta["playwright_page"]
            await page.close()
            if request.meta["playwright_context"]:
                await page.context.close()

    async def extract_board_urls(self, response: Response):
        self.logger.info("Scraping boards")
        page: Page = response.meta["playwright_page"]

        async with BoardGridView(page, self.settings) as view:
            await view.start_view()
        board_urls = view.get_board_urls()
        self.logger.info(f"Found {len(board_urls)} boards for query {self.query}")  # type: ignore
        self.board_count = len(board_urls)

        for url in board_urls:
            meta = self.get_playwright_request_meta(new_context=True)
            yield response.follow(
                url,
                meta=meta,
                callback=self.extract_pin_urls,
                errback=self.errback_close_page,
            )

    async def extract_pin_urls(self, response: TextResponse):
        self.logger.info(f'Scraping pins from board. Url "{response.url}"')
        page: Page = response.meta["playwright_page"]

        async with PinGridView(page, self.settings, close_context=True) as view:
            await view.start_view()
        pin_urls = view.get_pin_urls()

        self.scraped_boards_count += 1
        self.pin_count += len(pin_urls)
        self.logger.info(f"Found {len(pin_urls)} pins for board {response.url}")
        self.logger.info(
            f"Boards scraped count={self.scraped_boards_count} out of {self.board_count}"
        )

        board_url = response.url
        board_title = response.css(".R-d::text").get()
        for url in pin_urls:
            yield response.follow(
                url,
                callback=self.parse_pin,
                cb_kwargs={
                    "board_url": board_url,
                    "board_title": board_title,
                },
            )

    async def parse_pin(self, response: TextResponse, board_url: str, board_title: str):
        pin_url = response.url
        try:
            json_data = re.search(
                r'<script data-relay-response="true" type="application\/json">(.+?)<\/script>',
                response.text,
                flags=re.S,
            ).group(1)

            data = json.loads(json_data)
            data = data["response"]["data"]["v3GetPinQuery"]["data"]

            self.scraped_pins_count += 1
            self.logger.info(f"Pin scraped. Url: {pin_url}")
            self.logger.info(
                f"Pins scraped count={self.scraped_pins_count} out of {self.pin_count}"
            )

            image_url = data["imageLargeUrl"]
            if not image_url:
                self.logger.info(f"Pin {pin_url} has no image url")
                return

            yield {
                "board_url": board_url,
                "board_title": board_title,
                "pin_url": pin_url,
                "title": data["title"],
                "description": data["closeupUnifiedDescription"],
                "image_urls": [image_url],
            }
        except (KeyError, AttributeError, JSONDecodeError) as e:
            self.logger.error(f"Error parsing pin {pin_url}: {repr(e)}")
            return
