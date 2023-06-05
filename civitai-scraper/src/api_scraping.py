import json
import sqlite3
import time
from typing import Optional

import settings
from src import client
from src.db import DB


class Scraper:
    def __init__(self) -> None:
        self._db = DB()
        self.api_url = "https://civitai.com/api/v1/images"
        self._client = client.Client()
        self._job: Optional[sqlite3.Row] = None
        self._current_page: Optional[int] = None

    def _make_requests(self) -> None:
        while True:
            params = {"limit": self._job["page_size"], "page": self._current_page}
            print(f"Scraping page n {params['page']}")
            response = self._client.make_request(self.api_url, params=params)
            response = response.json()

            for image_data in response["items"]:
                self._db.insert_image(
                    image_id=image_data["id"], response=json.dumps(image_data)
                )

            is_last_page = self._current_page == response["metadata"]["totalPages"]
            if is_last_page:
                self._db.update_job_status(1)
                print("Job completed.")
                break

            self._current_page += 1
            # sleep between requests
            time.sleep(settings.DOWNLOAD_DELAY)

    def start_scraping(self) -> None:
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
            self._client.close()
