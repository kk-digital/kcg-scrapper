import hashlib
from os import path

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
        if failure.check(SessionExpired):
            return self.start_requests()

        raise failure

    def start_requests(self):
        yield FormRequest(
            url="https://www.waynemadsenreport.com/?action=login",
            formdata={
                "username": self.settings["LOGIN_EMAIL"],
                "password": self.settings["LOGIN_PASSWORD"],
            },
            meta={"login_request": True},
        )

        yield Request(url="https://www.waynemadsenreport.com/sitemap")

    def parse(self, response: TextResponse):
        filename = hashlib.sha1(response.url.encode()).hexdigest() + ".html"
        filename = path.join(self.settings["HTML_OUTPUT_DIR"], filename)
        with open(filename, "wb") as fp:
            fp.write(response.body)

        file_urls = response.css("img::attr(src)").getall()
        file_urls = [response.urljoin(url) for url in file_urls]

        return dict(
            url=response.url,
            title=response.css("h2#main-title::text").get(),
            html_filename=filename,
            file_urls=file_urls,
        )
