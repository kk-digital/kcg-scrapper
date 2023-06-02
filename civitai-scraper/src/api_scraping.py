import json
import sqlite3
import time
from typing import Optional

import settings
from src.db import DB
import requests


class Scraper:
    def __init__(self) -> None:
        self._db = DB()
        self.api_url = "https://civitai.com/api/v1/images"
        self._job: Optional[sqlite3.Row] = None
        self._current_page: Optional[int] = None

    def start_scraping(self) -> None:
        # todo add proxy
        # todo check if session works
        # todo add excepts http error and timeout
        job = self._db.get_job()
        if not job:
            self._db.start_job()
            job = self._db.get_job()
        elif job["done"]:
            print("Job already completed.")
            return
        self._job = job
        self._current_page = self._job["current_page"]

        try:
            self._make_requests()
        finally:
            self._db.update_job_current_page(self._current_page)
            self._db.close()

    def _make_requests(self) -> None:
        while True:
            params = {"limit": self._job["page_size"], "page": self._current_page}
            response = requests.get(self.api_url, params=params)
            response = response.json()

            for image_data in response["items"]:
                self._db.insert_image(
                    image_id=image_data["id"], response=json.dumps(image_data)
                )

            self._current_page += 1
            # last page return 500
            is_last_page = self._current_page == response["metadata"]["totalPages"] - 1
            if is_last_page:
                self._db.update_job_status(1)
                print("Job completed.")
                break

            # sleep between requests
            time.sleep(settings.DOWNLOAD_DELAY)
