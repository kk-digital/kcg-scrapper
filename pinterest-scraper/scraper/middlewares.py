from scrapy import Request
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware


class CustomUserAgentMiddleware(UserAgentMiddleware):
    def process_request(self, request: Request, spider):
        if request.meta.get("playwright") == True:
            return None

        return super().process_request(request, spider)
