import logging
import time

from scrapy.exceptions import IgnoreRequest
from scrapy.http import Request, Response, TextResponse

from waynemadsen_scraper.spiders.waynemadsenreport_follow_all_pages import (
    WaynemadsenreportFollowAllPagesSpider as Spider,
)


class CheckSession:
    performing_login = True
    logger = logging.getLogger(__name__)
    pending_requests = []
    last_login_timestamp = 0

    def process_request(self, request: Request, spider: Spider):
        request.meta["timestamp"] = time.time_ns()

        if self.performing_login and not request.meta.get("login_request"):
            self.pending_requests.append(request)
            raise IgnoreRequest("Ignoring request while logging in.")

        return None

    def process_response(self, request: Request, response: Response, spider: Spider):
        if not isinstance(response, TextResponse):
            return response

        is_login_request = request.meta.get("login_request")

        if "This page is available to members only" in response.text:
            if not is_login_request:
                if self.performing_login:
                    self.pending_requests.append(request)
                    raise IgnoreRequest("Ignoring request while logging in.")
                if self.last_login_timestamp > request.meta["timestamp"]:
                    request.dont_filter = True
                    return request

            self.performing_login = True
            login_request = spider.get_login_request()
            if is_login_request:
                self.logger.info("Login failed, retrying.")
            else:
                self.pending_requests.append(request)
                self.logger.info("Session expired, logging in.")
            return login_request

        if is_login_request:
            self.last_login_timestamp = time.time_ns()
            self.performing_login = False
            request.meta["pending_requests"] = self.pending_requests
            self.pending_requests = []

        return response
