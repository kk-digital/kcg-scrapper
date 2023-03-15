import os
import scrapy
from scrapy.selector import Selector
import xml.etree.ElementTree as ET
import scrapy_warcio

class VginsightsSpider(scrapy.Spider):
    os.environ['SCRAPY_WARCIO_SETTINGS'] = 'kcg/warcio/settings.yml'
    name = "VginsightsCrawl"
    links_arr = []
    warcio = scrapy_warcio.ScrapyWarcIo()
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

        response.request.meta['WARC-Date'] = scrapy_warcio.warc_date()
        self.warcio.write(response, response.request)
        
        item[response.url] = self.links_arr
        yield item

        