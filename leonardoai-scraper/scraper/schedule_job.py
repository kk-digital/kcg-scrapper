import threading
import time
from multiprocessing import Process
from pathlib import Path

import schedule
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from utils.export import run as export_util


def run_spider():
    print("Running spider")

    def crawl():
        process = CrawlerProcess(get_project_settings())
        process.crawl("leonardo-showcase")
        process.start()

    p = Process(target=crawl)
    p.start()
    p.join()
    print("Spider finished")


def run_export():
    print("Running export")

    def export():
        jsonl_path = Path("output/generations.jsonl")
        if not jsonl_path.exists():
            print("No generations.jsonl file found")
            return

        jsonl_path = jsonl_path.rename("output/generations-to-export.jsonl")
        export_util("output", str(jsonl_path), "output/images/full/")
        print("Export finished")

    job_thread = threading.Thread(target=export)
    job_thread.start()


schedule.every().friday.do(run_export)
schedule.every(3).minutes.do(run_spider)


while True:
    schedule.run_pending()
    time.sleep(1)
