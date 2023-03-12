import scrapy


class ExampleSpider(scrapy.Spider):
    name = "commoncrawl"
    allowed_domains = ["https://vginsights.com/"]
    start_urls = ["https://vginsights.com/"]

    def parse(self, response):
        pass
