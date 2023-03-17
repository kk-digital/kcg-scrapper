import os
import scrapy
from scrapy.selector import Selector
import xml.etree.ElementTree as ET
from playwright.async_api import async_playwright
from scrapy_playwright.page import PageMethod
import requests


class VginsightsSpider(scrapy.Spider):
    os.environ['SCRAPY_WARCIO_SETTINGS'] = 'scrapper/warcio/settings.yml' # config warc config path  
    name = "VginsightsCrawl"
    links_arr = []
    start_urls = ["https://vginsights.com/game/33750"]
    x = requests.get('https://vginsights.com/sitemap.xml')

    def start_requests(self):
        # response = requests.get('https://vginsights.com/sitemap.xml')
        # tree = ET.fromstring(response.content)
        # for child in tree:
        #     link1 = child[0].text
        #     response1 = requests.get(link1)
        #     tree1 = ET.fromstring(response1.content)
        #     for child in tree1:
        #         link2 = child[0].text
        #         self.links_arr.append(link2)
        self.links_arr = ["https://vginsights.com/game/33750"]

        for url in self.links_arr:
            print("🐍 File: spiders/vginsights_crawl.py | Line: 30 | start_requests ~ url",url)

            yield scrapy.Request(url, meta=dict(
                    playwright = True,
                    playwright_include_page = True, 
                    playwright_page_methods =[PageMethod("wait_for_timeout", 4000)]),
                    callback=self.get_page,
                    errback=self.close_context_on_error,)


    async def get_page(self, response): # scrap sublinks one by one 

        page = response.meta["playwright_page"]
        await page.close()
        dir_path = "data/vginsights.com/html"
        url_path = response.request.url
        name = url_path.split("/")[3:-1]
        file_name = '_'.join(name) + ".html"
   
        file_path = os.path.join(dir_path, file_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        if not os.path.exists(file_path):
            f = open(file_path, "x")
            f.write(response.text)
            f.close()

        yield None
        
    async def close_context_on_error(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.context.close()