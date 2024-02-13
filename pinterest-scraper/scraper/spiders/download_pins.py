import json
import re
from pathlib import Path
from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import TextResponse


class DownloadPinsSpider(Spider):
    name = "download-pins"
    allowed_domains = ["pinterest.com"]

    def start_requests(self) -> Iterable[Request]:
        self.pin_count = 0
        self.scraped_pins_count = 0
        urls_path = getattr(self, "urls_path")
        with Path(urls_path).open("r", encoding="utf-8") as fp:
            for url in fp:
                self.pin_count += 1
                yield Request(url)

    def parse(self, response: TextResponse):
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
                "pin_url": pin_url,
                "title": data["title"],
                "description": data["closeupUnifiedDescription"],
                "image_urls": [image_url],
            }
        except (KeyError, AttributeError, json.JSONDecodeError) as e:
            self.logger.error(f"Error parsing pin {pin_url}: {repr(e)}")
            return
