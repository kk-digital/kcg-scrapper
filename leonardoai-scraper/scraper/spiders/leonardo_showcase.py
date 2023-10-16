from playwright.async_api import Page

from scraper.views.login import LoginView
from scraper.views.showcase import ShowcaseView

import scrapy
from scrapy import Request


class LeonardoShowcaseSpider(scrapy.Spider):
    name = "leonardo-showcase"
    allowed_domains = ["leonardo.ai"]
    start_url = "https://leonardo.ai/"

    async def errback_close_page(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()

    async def init_page(self, page, request):
        await page.add_init_script(
            script="Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

    def start_requests(self):
        yield Request(
            self.start_url,
            meta=dict(
                playwright=True,
                playwright_include_page=True,
                playwright_page_init_callback=self.init_page,
            ),
            errback=self.errback_close_page,
        )

    async def parse(self, response):
        page: Page = response.meta["playwright_page"]
        async with page.context.expect_page() as new_page_info:
            await page.get_by_label("Launch App").click()
            self.logger.debug("Got to App page")

        new_page: Page = await new_page_info.value
        await ShowcaseView(new_page, self.settings).start_view()

        await page.close()
