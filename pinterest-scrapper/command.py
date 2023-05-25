import json
import logging
import os
from datetime import datetime
from os import path
from typing import Optional

import fire
from selenium.common import WebDriverException

import settings
from src import db, logging_config, utils
from src.board_stage import BoardStage
from src.download_stage import DownloadStage
from src.pin_stage import PinStage


class Command:
    def __init__(self) -> None:
        self.logger = logging.getLogger(f"scraper.{__name__}")
        self.start_args = {}
        logging_config.configure()

        # init db conn
        db.initialize()

    def show_jobs(self) -> None:
        jobs = db.get_all_jobs()
        if not jobs:
            print("No jobs created yet.")
            return

        for job in jobs:
            print(
                f'{job["id"]}. Job for query: {job["query"]}, in stage: {job["stage"]}.'
            )

    def delete_job(self, query: str) -> None:
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
    ) -> Optional[list]:
        job = db.get_or_create_job_by_query(query)

        if output:
            settings.OUTPUT_FOlDER = path.expanduser(output)
        if proxy_list:
            settings.PROXY_LIST_PATH = path.expanduser(proxy_list)

        stage = "board" if self.start_args.get("board_search") else job["stage"]
        stages = {
            "board": BoardStage,
            "pin": PinStage,
            "download": DownloadStage,
            "completed": None,
        }
        stage_cls = stages[stage]
        if not stage_cls:
            print("Job already completed.")
            return

        try:
            stage_instance = stage_cls(
                job=job, max_workers=max_workers, headless=not headed
            )
            result = stage_instance.start_scraping(**self.start_args)

            return result
        except WebDriverException:
            self.start_scraping(query, headed, max_workers, output, proxy_list)
        except:
            self.logger.critical(
                f'Unable to handle exception for query "{job["query"]}".',
                exc_info=True,
            )
            raise

    def start_scraping_list(
            self,
            query_list: str,
            headed: bool = False,
            max_workers: int = 1,
            output: str = None,
            proxy_list: str = None,
    ) -> None:
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
    ) -> None:
        self.start_args["board_search"] = True

        queries = utils.read_csv(query_list)
        output_rows = []
        for query in queries:
            query = query[0].strip()
            boards = self.start_scraping(
                query=query,
                headed=headed,
                output=output,
                proxy_list=proxy_list,
            )
            boards = [
                dict(url=board[1], title=board[2], pin_count=board[3])
                for board in boards
            ]
            output_rows.append(dict(query=query, boards=boards))

        total_board_count = 0
        unique_boards = set()
        total_pin_count = 0
        dict_order = {"query": 1, "board_count": 2, "pin_count": 3, "boards": 4}
        ordered_output_rows = []
        for row in output_rows:
            board_count = len(row["boards"])
            row["board_count"] = board_count
            total_board_count += board_count
            unique_boards.update([board["url"] for board in row["boards"]])
            pin_count = sum([board["pin_count"] for board in row["boards"]])
            row["pin_count"] = pin_count
            total_pin_count += pin_count
            ordered_output_rows.append(
                dict(sorted(row.items(), key=lambda x: dict_order[x[0]]))
            )

        output_path = path.join(
            settings.OUTPUT_FOlDER, f"board-search-{datetime.now().timestamp()}.json"
        )
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(
                dict(
                    total_board_count=total_board_count,
                    unique_board_count=len(unique_boards),
                    total_pin_count=total_pin_count,
                    results=ordered_output_rows,
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
    ) -> None:
        query = "test"
        job = db.get_job_by_query(query)

        if job:
            db.delete_job(job)

        db.create_job(query, "pin")
        job = db.get_job_by_query(query)
        db.create_many_board([(job["id"], url, "test title", 0)])

        try:
            self.start_scraping(
                query=query,
                headed=headed,
                max_workers=max_workers,
                output=output,
                proxy_list=proxy_list,
            )
        finally:
            db.delete_job(job)

    def delete_db(self) -> None:
        while True:
            answer = input(
                "Do you really want to to delete database and output folder? y/n: "
            )
            if answer == "n":
                return
            elif answer == "y":
                break

        try:
            os.remove(settings.DATABASE_NAME)
            print("Db deleted.")
        except FileNotFoundError:
            print("No db was found")


try:
    fire.Fire(Command)
finally:
    db.close_conn()
