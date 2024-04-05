import scrapy
from playwright.async_api import Page
from pymongo import MongoClient
from pymongo.collection import Collection
from scrapy import Request, signals
from scrapy.crawler import Crawler

from scraper.views.showcase import ShowcaseView


class LeonardoShowcaseSpider(scrapy.Spider):
    name = "leonardo-showcase"
    allowed_domains = ["leonardo.ai"]
    start_url = "https://leonardo.ai/"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client: MongoClient
        self.url_coll: Collection

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        self.client = MongoClient(self.settings["MONGO_URI"])
        db = self.client.leonardo_scraper
        self.url_coll = db.urls

    def spider_closed(self, spider, reason):
        self.client.close()

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

    def populate_image_urls(self, generations: list[dict]) -> list[dict]:
        for gen in generations:
            gen["image_urls"] = [gen["url"]]

        return generations

    def exclude_duplicates(self, generations: list[dict]) -> list[dict]:
        new_generations = []
        for gen in generations:
            doc = {"gen_id": gen["id"]}
            if not self.url_coll.find_one(doc):
                new_generations.append(gen)
                self.url_coll.insert_one(doc)
        return new_generations

    async def parse(self, response):
        page: Page = response.meta["playwright_page"]
        async with page.context.expect_page() as new_page_info:
            await page.get_by_label("Launch App").click()
            self.logger.debug("Got to App page")

        new_page: Page = await new_page_info.value
        generations = await ShowcaseView(new_page, self.settings).start_view()
        await page.close()
        generations = self.exclude_duplicates(generations)

        return self.populate_image_urls(generations)
