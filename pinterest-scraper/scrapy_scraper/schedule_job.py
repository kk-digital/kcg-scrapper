import time
from multiprocessing import Process

import schedule
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def job():
    print("Starting spider")

    def crawl():
        process = CrawlerProcess(get_project_settings())
        process.settings["FEEDS"] = {
            "output/data.csv": {
                "format": "csv",
                "encoding": "utf8",
                "overwrite": False,
            },
            "output/data.jsonl": {
                "format": "jsonlines",
                "encoding": "utf8",
                "overwrite": False,
            },
        }
        process.settings["JOBDIR"] = "output/jobdir"

        process.crawl("download-pins", urls_path="output/pin_urls.txt")
        process.start()

    p = Process(target=crawl)
    p.start()
    p.join()
    print("Spider finished")


schedule.every().day.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
