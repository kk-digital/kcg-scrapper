import hashlib
from io import BytesIO
from pathlib import Path
from typing import Iterable

import scrapy
from PIL import Image
from scrapy.http import Request, Response


class HfImagesSpider(scrapy.Spider):
    name = "hf-images"

    def start_requests(self) -> Iterable[Request]:
        self.images_store: Path = self.settings["IMAGES_STORE"] / "full"
        with open("urls.txt", "r", encoding="utf-8") as fp:
            for line in fp:
                yield Request(url=line.strip())

    def parse(self, response: Response):
        filename = hashlib.sha1(response.url.encode()).hexdigest() + ".jpg"
        file_path = self.images_store / filename
        try:
            with Image.open(BytesIO(response.body)) as img:
                rgb_img = img.convert("RGB")
                rgb_img.save(file_path, format="JPEG")

            yield {"url": response.url, "filename": "full/" + filename}

        except OSError:
            self.logger.info(f"Failed to save image: {response.url}")
