import json
import logging
from datetime import datetime
from os import path

import fire

import settings
from src import db, logging_config, utils


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
        **kwargs,
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
            from src.board_stage import BoardStage

            stage_cls = BoardStage
        elif stage == "pin":
            from src.pin_stage import PinStage

            stage_cls = PinStage
        elif stage == "download":
            from src.download_stage import DownloadStage

            stage_cls = DownloadStage
        else:
            print("Job already completed.")
            return

        try:
            stage_instance = stage_cls(
                job=job, max_workers=max_workers, headless=not headed
            )
            stage_instance.start_scraping(**kwargs)

            return job
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
        rows = utils.read_csv(query_list)
        for row in rows:
            self.start_scraping(
                query=row[0].strip(),
                headed=headed,
                max_workers=max_workers,
                output=output,
                proxy_list=proxy_list,
            )

    def board_search(
        self,
        query_list: str,
        headed: bool = False,
        output: str = None,
        proxy_list: str = None,
    ):
        query_rows = utils.read_csv(query_list)
        job_ids = []
        for query_row in query_rows:
            query = query_row[0].strip()
            job = db.get_job_by_query(query)
            if job and job['stage'] == 'pin':
                job_ids.append(job['id'])
                continue

            job = self.start_scraping(
                query=query,
                headed=headed,
                proxy_list=proxy_list,
                execute_next_stage=False,
            )
            job_ids.append(job["id"])

        output_rows = []
        total_board_count = 0
        total_pin_count = 0
        for id in job_ids:
            boards = db.get_all_board_or_pin_by_job_id("board", id)
            boards = [
                dict(
                    title=board["title"], url=board["url"], pin_count=board["pin_count"]
                )
                for board in boards
            ]
            board_count = len(boards)
            pin_count = sum([board["pin_count"] for board in boards])
            total_board_count += board_count
            total_pin_count += pin_count
            output_rows.append(
                dict(
                    query=query,
                    board_count=board_count,
                    total_pin_count=pin_count,
                    boards=boards,
                )
            )

        output_path = path.expanduser(output) if output else "."
        output_path = path.join(
            output_path, f"board-search-{datetime.now().timestamp()}.json"
        )
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(
                dict(
                    total_board_count=total_board_count,
                    total_pin_count=total_pin_count,
                    results=output_rows,
                ),
                fh,
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
        db.create_many_board([(job["id"], url, "test title", 0)])

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
