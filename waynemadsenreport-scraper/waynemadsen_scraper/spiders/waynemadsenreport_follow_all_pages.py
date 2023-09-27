import hashlib
from os import path

from scrapy.exceptions import IgnoreRequest
from scrapy.http import TextResponse, FormRequest, Request
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from twisted.python.failure import Failure

from waynemadsen_scraper.exceptions import SessionExpired


class WaynemadsenreportFollowAllPagesSpider(CrawlSpider):
    name = "waynemadsenreport-follow-all-pages"
    allowed_domains = ["waynemadsenreport.com"]

    rules = (
        Rule(
            link_extractor=LxmlLinkExtractor(
                restrict_css=[
                    "#portal-column-one",
                    "#midcol",
                ]
            ),
            callback="parse",
            errback="errback",
            follow=True,
        ),
    )

    login_count = 0
    page_count = 0

    def __init__(self, *args, email, password, html_output_dir, **kwargs):
        super().__init__(*args, **kwargs)
        self.email = email
        self.password = password
        self.html_output_dir = html_output_dir

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(
            crawler,
            *args,
            email=crawler.settings["LOGIN_EMAIL"],
            password=crawler.settings["LOGIN_PASSWORD"],
            html_output_dir=crawler.settings["HTML_OUTPUT_DIR"],
            **kwargs,
        )

        return spider

    def errback(self, failure: Failure):
        if failure.check(IgnoreRequest):
            return None

        if failure.check(SessionExpired):
            self.logger.info("Session expired, logging in again.")
            return self.get_login_request()

        raise failure

    def after_login(self, response: TextResponse):
        self.login_count += 1
        self.logger.info(f"Logged in successfully. Total login: {self.login_count}")
        self.logger.info(
            f"Resuming pending requests. Total: {len(response.meta['pending_requests'])}"
        )

        for request in response.meta["pending_requests"]:
            request.dont_filter = True
            yield request

    def get_login_request(self):
        return FormRequest(
            url="https://www.waynemadsenreport.com/?action=login",
            formdata={
                "username": self.email,
                "password": self.password,
            },
            meta={"login_request": True},
            callback=self.after_login,
            priority=9999,
            dont_filter=True,
        )

    def start_requests(self):
        yield self.get_login_request()
        yield Request(url="https://www.waynemadsenreport.com/sitemap")

    def parse(self, response: TextResponse):
        self.page_count += 1
        self.logger.info(f"Parsing page {self.page_count}: {response.url}")

        filename = hashlib.sha1(response.url.encode()).hexdigest() + ".html"
        filename = path.join(self.html_output_dir, filename)
        with open(filename, "wb") as fp:
            fp.write(response.body)

        image_urls = response.css("img::attr(src)").getall()
        image_urls = set([response.urljoin(url) for url in image_urls])

        return dict(
            url=response.url,
            title=response.css("h2#main-title::text").get(),
            html_filename=filename,
            image_urls=image_urls,
        )
