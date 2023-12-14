import ast
import hashlib
import urllib.parse
from pathlib import Path
from typing import Iterable

import scrapy
from scrapy.http import Request, TextResponse


class VideosSpider(scrapy.Spider):
    name = "videos"
    allowed_domains = ["altcensored.com"]

    def start_requests(self) -> Iterable[Request]:
        self.html_dir: Path = self.settings["HTML_DIR"]
        scraped_urls = getattr(self, "scraped_urls")
        if scraped_urls is not None:
            with open(scraped_urls, "r", encoding="utf-8") as fp:
                self.scraped_urls = ast.literal_eval(fp.read())

        yield Request("https://altcensored.com/")

    def parse(self, response: TextResponse):
        for anchor in response.css("h3 strong a"):
            yield response.follow(anchor)

        for url in response.css(".pure-u-md-1-4 a+ p a::attr(href)").getall():
            query_string = urllib.parse.urlsplit(url).query
            if query_string in self.scraped_urls:
                self.logger.info(f"Skipping url {url}")
                continue

            yield response.follow(url, callback=self.parse_video)

    def parse_video(self, response: TextResponse):
        html_filename = hashlib.sha1(response.url.encode()).hexdigest() + ".html"
        self.html_dir.joinpath(html_filename).write_bytes(response.body)
        torrent_link = response.css(
            ".pure-u-md-1-5 .h-box:nth-child(1) a:nth-child(3)::attr(href)"
        ).get()

        return {
            "url": response.url,
            "title": response.css("h2::text").get(),
            "category": response.css("p~ br+ a::text").get(),
            "html_filename": html_filename,
            "youtube_video_link": response.css(
                ".pure-u-md-1-5 .h-box:nth-child(1) a:nth-child(1)::attr(href)"
            ).get(),
            "torrent_link": torrent_link,
            "channel_name": response.css("h3 a::text").get(),
            "channel_link": response.urljoin(response.css("h3 a::attr(href)").get()),
        }
