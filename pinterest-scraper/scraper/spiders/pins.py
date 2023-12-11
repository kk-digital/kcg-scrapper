import hashlib
import itertools
import urllib.parse
from pathlib import Path
from typing import Iterable

import scrapy
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
        self.html_files_folder: Path = self.settings["HTML_FILES_FOLDER"]
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

    async def extract_pin_urls(self, response: Response):
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

        for url in pin_urls:
            meta = self.get_playwright_request_meta(new_context=True)
            yield response.follow(
                url,
                callback=self.parse_pin,
                errback=self.errback_close_page,
                meta=meta,
            )

    async def parse_pin(self, response: TextResponse):
        self.logger.info(f"Scraping pin. Url {response.url}")
        page: Page = response.meta["playwright_page"]
        await page.close()
        await page.context.close()

        pin_html = response.css(".hs0 > .zI7 > .XiG").get()
        image_url = response.css(".PcK .hCL::attr(src)").get()
        if pin_html is None or image_url is None:
            return

        image_url_parsed = urllib.parse.urlparse(image_url)
        image_url_path_parts = image_url_parsed.path.split("/")
        image_url_path_parts[1] = "originals"
        image_url_parsed = image_url_parsed._replace(
            path="/".join(image_url_path_parts)
        )
        image_url = urllib.parse.urlunparse(image_url_parsed)

        html_filename = hashlib.sha1(response.url.encode()).hexdigest() + ".html"
        self.html_files_folder.joinpath(html_filename).write_text(
            pin_html, encoding="utf-8"
        )

        self.scraped_pins_count += 1
        self.logger.info(f"Pin scraped. Url: {response.url}")
        self.logger.info(
            f"Pins scraped count={self.scraped_pins_count} out of {self.pin_count}"
        )

        yield {"html_filename": html_filename, "image_urls": [image_url]}
