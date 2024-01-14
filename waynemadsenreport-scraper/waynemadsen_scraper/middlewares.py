import logging
import time

from scrapy.http import Request, Response, TextResponse

from waynemadsen_scraper.spiders.waynemadsenreport_follow_all_pages import (
    WaynemadsenreportFollowAllPagesSpider as Spider,
)


class CheckSession:
    performing_login = True
    logger = logging.getLogger(__name__)
    last_login_timestamp = 0

    def process_request(self, request: Request, spider: Spider):
        request.meta["timestamp"] = time.time_ns()

        return None

    def process_response(self, request: Request, response: Response, spider: Spider):
        if not isinstance(response, TextResponse):
            return response

        is_login_request = request.meta.get("login_request")

        if is_login_request:
            self.performing_login = False
            self.last_login_timestamp = time.time_ns()
            return response

        if "This page is available to members only" in response.text:
            if (
                self.performing_login
                or self.last_login_timestamp > request.meta["timestamp"]
            ) and not is_login_request:
                request.dont_filter = True
                return request

            self.performing_login = True
            login_request = spider.get_login_request()
            if is_login_request:
                login_request.meta["pending_request"] = request.meta.get(
                    "pending_request", None
                )
                self.logger.info("Login failed, retrying.")
            else:
                login_request.meta["pending_request"] = request
                self.logger.info("Session expired, logging in.")
            return login_request

        return response
