import csv
import logging
from os import path

import fire

import logging_config
import settings
from pinterest_scraper import db


class Command:
    def __init__(self):
        logging_config.configure()
        self.logger = logging.getLogger(f"scraper.{__name__}")

        # init db conn
        db.initialize()

    def show_jobs(self):
        jobs = db.get_all_jobs()
        if not jobs:
            print("No jobs created yet.")
            return

        for job in jobs:
            print(
                f'{job["id"]}. Job for query: {job["query"]}, in stage: {job["stage"]}.'
            )

    def delete_job(self, query: str):
        job = db.get_job_by_query(query)

        if not job:
            print("There is no job for query.")
            return

        db.delete_job(job)
        print("Successfully deleted.")

    def start_scraping(
        self,
        query: str,
        headed: bool = False,
        max_workers: int = 1,
        output: str = None,
        proxy_list: str = None,
    ):
        job = db.get_job_by_query(query)

        if not job:
            self.logger.info(f"Job created for query: {query}.")
            db.create_job(query)
            job = db.get_job_by_query(query)

        if output:
            settings.OUTPUT_FOlDER = path.expanduser(output)
        if proxy_list:
            settings.PROXY_LIST_PATH = path.expanduser(proxy_list)

        stage = job["stage"]
        if stage == "board":
            from pinterest_scraper.board_stage import BoardStage

            stage_cls = BoardStage
        elif stage == "pin":
            from pinterest_scraper.pin_stage import PinStage

            stage_cls = PinStage
        elif stage == "download":
            from pinterest_scraper.download_stage import DownloadStage

            stage_cls = DownloadStage
        else:
            print("Job already completed.")
            return

        try:
            stage_instance = stage_cls(
                job=job, max_workers=max_workers, headless=not headed
            )
            stage_instance.start_scraping()
        except:
            self.logger.critical(
                f'Unable to handle exception on {stage_cls.__name__}, for query "{job["query"]}".',
                exc_info=True,
            )

    def start_scraping_list(
        self,
        query_list: str,
        headed: bool = False,
        max_workers: int = 1,
        output: str = None,
        proxy_list: str = None,
    ):
        with open(query_list, "r", newline="", encoding="utf-8") as fh:
            csv_reader = csv.reader(fh)
            for row in csv_reader:
                self.start_scraping(
                query=row[0].strip(),
                headed=headed,
                max_workers=max_workers,
                output=output,
                proxy_list=proxy_list,
            )

    def test_scrape_board(
        self,
        url: str,
        headed: bool = False,
        max_workers: int = 1,
        output: str = None,
        proxy_list: str = None,
    ):
        query = "test"
        job = db.get_job_by_query(query)

        if job:
            db.delete_job(job)

        db.create_job(query, "pin")
        job = db.get_job_by_query(query)
        db.create_many_board([(job["id"], url)])

        self.start_scraping(
            query=query,
            headed=headed,
            max_workers=max_workers,
            output=output,
            proxy_list=proxy_list,
        )
        db.delete_job(job)


try:
    fire.Fire(Command)
finally:
    db.close_conn()
