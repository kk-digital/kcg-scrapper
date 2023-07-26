import json
from typing import Optional

from scrapy import Spider
from scrapy.http import Request, TextResponse


class PromptsSpider(Spider):
    name = "prompts"
    allowed_domains = ["openart.ai"]
    url = "https://openart.ai/api/search?source=any&type=both&query={}&cursor={}"

    def __init__(self, query: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query = query

    def start_requests(self):
        yield Request(self.url.format(self.query, ""), callback=self.parse)

    def parse(self, response: TextResponse):
        data = json.loads(response.text)
        cursor = data.get("nextCursor")
        if cursor:
            yield response.follow(self.url.format(self.query, cursor))

        for item in data["items"]:
            if not item["image_url"] in item.setdefault("image_urls", []):
                item["image_urls"].append(item["image_url"])

            yield item
