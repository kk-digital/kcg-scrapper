import scrapy


class PostsSpider(scrapy.Spider):
    name = "posts"
    allowed_domains = ["haidut.me"]
    start_urls = ["http://haidut.me/"]

    def parse(self, response):
        pass
