import json
import os
import sqlite3
import time
from typing import Optional

import tenacity

import settings
from src.client import Client
from src.db import DB
from src.download_images import ImageDownloader


class Scraper:
    def __init__(self) -> None:
        self._db = DB()
        self.api_url = "https://civitai.com/api/v1/images"
        self._client = Client()
        self._image_downloader = ImageDownloader(self._client, self._db)
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
                break

            self._current_page += 1
            # sleep between requests
            time.sleep(settings.DOWNLOAD_DELAY)

    def start_scraping(self) -> None:
        job = self._db.get_job()
        if not job:
            self._db.start_job()
            job = self._db.get_job()
        self._job = job
        self._current_page = self._job["current_page"]

        try:
            for attempt in tenacity.Retrying(wait=tenacity.wait_fixed(settings.RETRY_DELAY)):
                with attempt:
                    self._make_requests()
                    self._image_downloader.start_download()
        except:
            raise
        finally:
            self._db.update_job_current_page(self._current_page)
            self._db.close()
            self._client.close()
            self._image_downloader.close()
