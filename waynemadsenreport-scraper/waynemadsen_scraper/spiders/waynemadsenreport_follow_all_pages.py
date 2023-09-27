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

    def errback(self, failure: Failure):
        if failure.check(IgnoreRequest):
            return None

        if failure.check(SessionExpired):
            return self.get_login_request()

        raise failure

    def after_login(self, response: TextResponse):
        for request in response.meta["pending_requests"]:
            request.dont_filter = True
            yield request

    def get_login_request(self):
        return FormRequest(
            url="https://www.waynemadsenreport.com/?action=login",
            formdata={
                "username": self.settings["LOGIN_EMAIL"],
                "password": self.settings["LOGIN_PASSWORD"],
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
        filename = hashlib.sha1(response.url.encode()).hexdigest() + ".html"
        filename = path.join(self.settings["HTML_OUTPUT_DIR"], filename)
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
