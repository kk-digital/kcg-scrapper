import logging

from scrapy import Spider
from scrapy.exceptions import IgnoreRequest
from scrapy.http import Response, TextResponse, Request

from waynemadsen_scraper.exceptions import SessionExpired


class CheckSession:
    performing_login = True
    pending_requests = []
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
                request.meta["pending_requests"] = self.pending_requests
                self.pending_requests = []

                return response

            self.logger.info("Retrying login.")
            return request

        if "This page is available to members only" in response.text:
            if self.performing_login:
                self.pending_requests.append(request)
                raise IgnoreRequest("Waiting for login to complete.")

            self.performing_login = True
            raise SessionExpired("Need to renew session.")

        return response
