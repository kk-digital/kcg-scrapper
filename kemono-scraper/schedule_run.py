import shutil
import time
from datetime import date
from pathlib import Path

import schedule
from command import Command
from fire import Fire
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def daily_run(settings):
    process = CrawlerProcess(settings)
    process.crawl("posts")
    process.start(stop_after_crawl=False)


def compress_output_every_friday(settings, jsonl_path):
    Command().compress_output(str(jsonl_path))

    weekly_folder = Path(
        settings["OUTPUT_FOLDER"], f"kemono-scraper-output-{date.today().isoformat()}"
    )
    weekly_folder.mkdir()

    shutil.move(jsonl_path, weekly_folder)

    for zipfile in Path(settings["OUTPUT_FOLDER"]).glob("*.zip"):
        shutil.move(zipfile, weekly_folder)

    shutil.make_archive(
        base_name=str(weekly_folder), format="zip", root_dir=weekly_folder
    )
    shutil.rmtree(weekly_folder)


def main(
    jsonl_path: str,
    job_dir: str | None = None,
    run_now: bool = False,
    exit_on_finish: bool = False,
):
    settings = get_project_settings()
    settings["FEEDS"] = {
        jsonl_path: {
            "format": "jsonlines",
            "overwrite": False,
        }
    }
    settings["JOBDIR"] = job_dir if job_dir else ""

    if run_now:
        compress_output_every_friday(settings, jsonl_path)
        if exit_on_finish:
            return

    schedule.every().day.at("12:00").do(daily_run, settings)
    schedule.every().saturday.do(compress_output_every_friday, settings, jsonl_path)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    Fire(main)
