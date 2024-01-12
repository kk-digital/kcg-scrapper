import logging

from scrapy.http import Request, Response, TextResponse

from waynemadsen_scraper.spiders.waynemadsenreport_follow_all_pages import (
    WaynemadsenreportFollowAllPagesSpider as Spider,
)


class CheckSession:
    performing_login = True
    logger = logging.getLogger(__name__)

    def process_response(self, request: Request, response: Response, spider: Spider):
        if not isinstance(response, TextResponse):
            return response

        if request.meta.get("login_request"):
            if (
                response.css("#loginform").get() is None
                or "Exclusive Content" in response.text
            ):
                self.performing_login = False
                return response

        if "This page is available to members only" in response.text:
            if self.performing_login:
                request.dont_filter = True
                return request

            self.performing_login = True
            login_request = spider.get_login_request()
            login_request.meta["pending_request"] = request
            self.logger.info("Retrying login.")
            return login_request

        return response
