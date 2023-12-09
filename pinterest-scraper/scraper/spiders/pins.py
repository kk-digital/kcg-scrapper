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

    def start_requests(self) -> Iterable[Request]:
        self.proxy_list_cycle = itertools.cycle(utils.load_proxies())
        self.html_files_folder: Path = self.settings["HTML_FILES_FOLDER"]

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
            "proxy": None,
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

    async def errback_close_page(self, failure):
        request = failure.request
        self.logger.info(f"There was a problem scraping {request.url}")
        self.logger.error(repr(failure))
        page = request.meta["playwright_page"]
        await page.close()
        if request.meta["playwright_context"]:
            await page.context.close()

    async def extract_board_urls(self, response: Response):
        page: Page = response.meta["playwright_page"]

        view = BoardGridView(page, self.settings)
        await view.start_view()
        board_urls = view.get_board_urls()
        self.logger.info(f"Found {len(board_urls)} boards for query {self.query}")  # type: ignore
        await page.close()

        for url in board_urls:
            meta = self.get_playwright_request_meta(new_context=True)
            yield response.follow(
                url,
                meta=meta,
                callback=self.extract_pin_urls,
                errback=self.errback_close_page,
            )

    async def extract_pin_urls(self, response: Response):
        page: Page = response.meta["playwright_page"]

        view = PinGridView(page, self.settings)
        await view.start_view()
        pin_urls = view.get_pin_urls()
        self.logger.info(f"Found {len(pin_urls)} pins for board {response.url}")
        await page.close()
        await page.context.close()

        for url in pin_urls:
            meta = self.get_playwright_request_meta(new_context=True)
            yield response.follow(
                url,
                callback=self.parse_pin,
                errback=self.errback_close_page,
                meta=meta,
            )

    async def parse_pin(self, response: TextResponse):
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

        self.logger.info(f"Pin scraped. Url: {response.url}")

        yield {"html_filename": html_filename, "image_urls": [image_url]}
