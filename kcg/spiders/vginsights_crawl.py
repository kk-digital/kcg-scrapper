import os
import scrapy
from scrapy.selector import Selector
import xml.etree.ElementTree as ET

class VginsightsSpider(scrapy.Spider):
    os.environ['SCRAPY_WARCIO_SETTINGS'] = 'kcg/warcio/settings.yml'
    name = "VginsightsCrawl"
    links_arr = []
    # allowed_domains = ["https://vginsights.com/sitemap.xml"]
    start_urls = ["https://vginsights.com/sitemap.xml"]

    def parse(self, response):
        obj = Selector(response).extract()
        root = ET.fromstring(obj)
        for child in root:
            link = child[0].text

            yield scrapy.Request(url=link, callback=self.reparse)
            
    def reparse(self, response):
        item = {}
        obj = Selector(response).extract()
        root = ET.fromstring(obj)
        for child in root:
            link = child[0].text
            self.links_arr.append(link)

        item[response.url] = self.links_arr
        yield item

        