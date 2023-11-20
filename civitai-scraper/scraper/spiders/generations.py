from typing import Iterable

import scrapy
from scrapy import Request
from scrapy.http import TextResponse


class GenerationsSpider(scrapy.Spider):
    name = "generations"
    allowed_domains = ["civitai.com"]

    def start_requests(self) -> Iterable[Request]:
        url = "https://civitai.com/api/v1/images"
        cursor = getattr(self, "cursor", None)
        if cursor is not None:
            url += f"?cursor={cursor}"

        yield Request(url=url, callback=self.parse)

    def parse(self, response: TextResponse):
        data = response.json()

        next_url = data["metadata"].get("nextPage", None)
        if next_url:
            self.logger.info(f"Next url to scrape {next_url}")
            yield Request(url=next_url, callback=self.parse)

        generations: list[dict] = data["items"]
        for gen in generations:
            gen["image_urls"] = [gen["url"]]

            yield gen
