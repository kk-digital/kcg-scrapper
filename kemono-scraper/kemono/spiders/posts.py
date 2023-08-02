import hashlib
from pathlib import Path

from scrapy import Spider
from scrapy.http import TextResponse


class PostsSpider(Spider):
    name = "posts"
    allowed_domains = ["kemono.party"]
    start_urls = ["https://www.kemono.party/posts?o=0"]
    count = 0

    # noinspection PyMethodOverriding
    def parse(self, response: TextResponse):
        yield from response.follow_all(
            css=".post-card--preview a", callback=self.parse_post
        )

        next_page = response.css("#paginator-top .next::attr(href)").get()
        if next_page:
            yield response.follow(next_page)

    def parse_post(self, response: TextResponse):
        html_name = hashlib.sha1(response.url.encode()).hexdigest() + ".html"
        html_path = Path(self.settings["FILES_STORE"], html_name)
        html_path.write_bytes(response.body)

        images = [
            "https:" + src
            if src.startswith("//")
            else "https://c4.kemono.party/data" + src
            for src in response.css("#page img::attr(src)").getall()
        ]

        yield dict(
            url=response.url,
            html_file=html_path.name,
            image_urls=images,
        )
