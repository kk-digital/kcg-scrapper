import os
import scrapy
from scrapy.selector import Selector
import xml.etree.ElementTree as ET

class VginsightsSpider(scrapy.Spider):
    os.environ['SCRAPY_WARCIO_SETTINGS'] = 'scrapper/warcio/settings.yml' # config warc config path  
    name = "VginsightsCrawl"
    links_arr = []
    start_urls = ["https://vginsights.com/sitemap.xml"]

    def parse(self, response): # Get Main links
        obj = Selector(response).extract()
        root = ET.fromstring(obj)
        for child in root:
            link = child[0].text
            yield scrapy.Request(url=link, callback=self.reparse)
            
    def reparse(self, response): # Get sublinks
        item = {}
        obj = Selector(response).extract()
        root = ET.fromstring(obj)
        for child in root:
            link = child[0].text
            yield scrapy.Request(url=link, callback=self.get_page)


    def get_page(self, response): # scrap sublinks one by one 
        item = {}
        item["url"] = response.url
        #-----------------------
        # add in this place name, id ...........
        #-----------------------
        yield item
        
        