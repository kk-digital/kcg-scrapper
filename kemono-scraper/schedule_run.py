import shutil
from pathlib import Path

import schedule
import time
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import sys
from command import Command
from datetime import date

jsonl_path = Path(sys.argv[1])
settings = get_project_settings()
settings["FEEDS"] = {
    jsonl_path: {
        "format": "jsonlines",
        "overwrite": False,
    }
}


def daily_run():
    process = CrawlerProcess(settings)
    process.crawl("posts")
    process.start()


def compress_output_every_friday():
    Command().compress_output(str(jsonl_path))

    weekly_folder = Path(
        settings["OUTPUT_FOLDER"], f"kemono-scraper-output-{date.today().isoformat()}"
    )
    weekly_folder.mkdir()

    shutil.move(jsonl_path, weekly_folder)
    shutil.move(settings["FILES_STORE"], weekly_folder)
    shutil.move(settings["IMAGES_STORE"], weekly_folder)

    shutil.make_archive(
        base_name=str(weekly_folder), format="zip", root_dir=weekly_folder
    )
    weekly_folder.unlink()


schedule.every().day.at("12:00").do(daily_run)
schedule.every().friday.do(compress_output_every_friday)

while True:
    schedule.run_pending()
    time.sleep(1)
