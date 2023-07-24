from typing import Optional

from scrapy import Spider
from scrapy.http import Request, TextResponse


class PromptsSpider(Spider):
    name = "prompts"
    allowed_domains = ["openart.ai"]

    def __init__(self, query: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query = query

    def start_requests(self):
        url = f"https://openart.ai/api/search?source=any&type=both&query={self.query}&cursor="
        yield Request(url)

    def parse(self, response: TextResponse):
        print(response.url, response.status)
