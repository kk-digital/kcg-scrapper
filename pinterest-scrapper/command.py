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

    def start_scraping(self, query: str, headed: bool = False, output: str = None):
        job = db.get_job_by_query(query)

        if not job:
            self.logger.info(f"Job created for query: {query}.")
            db.create_job(query)
            job = db.get_job_by_query(query)

        if output:
            settings.OUTPUT_FOlDER = path.expanduser(output)

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
            stage_instance = stage_cls(job, headless=not headed)
            stage_instance.start_scraping()
        except:
            self.logger.critical(
                f'Unable to handle exception on {stage_cls.__name__}, for query "{job["query"]}".',
                exc_info=True,
            )
        finally:
            # noinspection PyUnboundLocalVariable
            stage_instance.close()

    def test_scrape_board(self, url: str, headed: bool = False, output: str = None):
        query = 'test'
        job = db.get_job_by_query(query)

        if job:
            db.delete_job(job)

        db.create_job(query, 'pin')
        job = db.get_job_by_query(query)
        db.create_many_board([(job['id'], url)])

        self.start_scraping(query, headed, output)

    def __del__(self):
        db.close_conn()


fire.Fire(Command)
