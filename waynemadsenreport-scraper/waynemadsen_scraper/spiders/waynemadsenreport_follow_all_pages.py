import hashlib
from pathlib import Path

from scrapy.http import FormRequest, Request, TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class WaynemadsenreportFollowAllPagesSpider(CrawlSpider):
    name = "waynemadsenreport-articles"

    rules = [
        Rule(
            LinkExtractor(
                allow=[r"\/articles"],
                restrict_css=["#columnswrapper"],
            ),
            callback="parse_article",
            follow=True,
        ),
        Rule(
            LinkExtractor(
                deny=[r"\/calendar", "#calendar"],
                restrict_css=["#columnswrapper"],
            ),
        ),
    ]

    login_count = 0
    article_count = 0

    def after_login(self, response: TextResponse):
        self.login_count += 1
        self.logger.info(f"Logged in successfully. Total login: {self.login_count}")
        self.logger.info(f"Resuming pending request.")

        pending_request = response.meta.get("pending_request")
        if pending_request is not None:
            pending_request.dont_filter = True
            yield pending_request

    def get_login_request(self):
        return FormRequest(
            url="https://www.waynemadsenreport.com/?action=login",
            formdata={
                "username": self.email,
                "password": self.password,
            },
            meta={"login_request": True},
            callback=self.after_login,
            dont_filter=True,
        )

    def start_requests(self):
        self.email = self.settings["LOGIN_EMAIL"]
        self.password = self.settings["LOGIN_PASSWORD"]
        self.html_dir: Path = self.settings["HTML_DIR"]

        yield self.get_login_request()
        yield Request(url="https://www.waynemadsenreport.com/sitemap")

    def parse_article(self, response):
        self.article_count += 1
        self.logger.info(f"Parsing article {self.article_count}: {response.url}")

        filename = hashlib.sha1(response.url.encode()).hexdigest() + ".html"
        content = response.css(".documentContent").get()
        self.html_dir.joinpath(filename).write_text(content, encoding="utf-8")

        title = response.css("h2#main-title::text").get()
        pub_date = response.css("#pubdate span::text").get()

        return dict(
            url=response.url,
            title=title,
            pub_date=pub_date,
            html_filename="full/" + filename,
        )
