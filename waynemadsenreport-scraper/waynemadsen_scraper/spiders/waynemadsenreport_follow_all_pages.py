import hashlib
from pathlib import Path

from scrapy.http import FormRequest, TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class WaynemadsenreportFollowAllPagesSpider(CrawlSpider):
    name = "waynemadsenreport-articles"
    allowed_domains = ["waynemadsenreport.com"]
    start_urls = ["https://www.waynemadsenreport.com/sitemap"]

    rules = [
        Rule(
            LinkExtractor(
                allow=[r"\.com\/articles"],
                deny=[
                    "#calendar",
                    r"\/print",
                ],
                restrict_css=[".documentContent"],
            ),
            callback="parse_article",
            # follow=True,
        ),
    ]

    article_external_link_extractor = LinkExtractor(
        deny_domains="waynemadsenreport.com",
        restrict_css=".documentContent",
    )

    login_count = 0
    article_count = 0

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        settings = crawler.settings
        email = settings["LOGIN_EMAIL"]
        password = settings["LOGIN_PASSWORD"]
        html_dir = settings["HTML_DIR"]
        spider = super().from_crawler(
            crawler, email=email, password=password, html_dir=html_dir, *args, **kwargs
        )

        return spider

    def __init__(self, *a, email: str, password: str, html_dir: Path, **kw):
        super().__init__(*a, **kw)
        self.email = email
        self.password = password
        self.html_dir = html_dir

    def after_login(self, response: TextResponse):
        self.login_count += 1
        self.logger.info(f"Logged in successfully. Total login: {self.login_count}")
        pending_request = response.meta["pending_request"]
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
            priority=100,
        )

    def parse_article(self, response):
        self.article_count += 1
        self.logger.info(f"Parsing article {self.article_count}: {response.url}")

        filename = hashlib.sha1(response.url.encode()).hexdigest() + ".html"
        content = response.css(".documentContent").get()
        self.html_dir.joinpath(filename).write_text(content, encoding="utf-8")

        external_links = [
            link.url
            for link in self.article_external_link_extractor.extract_links(response)
        ]

        title = response.css("h2#main-title::text").get()
        pub_date = response.css("#pubdate span::text").get()

        yield {
            "url": response.url,
            "title": title,
            "pub_date": pub_date,
            "html_filename": "full/" + filename,
            "external_links": external_links,
        }
