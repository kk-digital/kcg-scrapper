import json
import logging
import os
from os import path
from pathlib import PurePosixPath

from playwright.sync_api import Page, Response
from sqlalchemy import select

import settings
from src.db import engine as db_engine

from src.db.model import Generation
from urllib.parse import urlparse


class ImageDownloader:
    def __init__(self, page: Page) -> None:
        engine = db_engine.get_engine()
        self._session = db_engine.get_session(engine)
        self._logger = logging.getLogger(f"scraper.{__name__}")
        self._page = page
        self._download_delay = settings.DOWNLOAD_DELAY
        # init images folder
        self._images_folder = path.join(settings.OUTPUT_FOLDER, "images")
        os.makedirs(self._images_folder, exist_ok=True)

    # todo implement retry
    def _make_request(self, url: str) -> Response:
        with self._page.expect_response(url) as response_info:
            self._page.goto(url)
        response = response_info.value
        code = response.status
        if code != 200:
            print("errorrrrr non 200 response")  # todo solve this

        return response

    def _save_image(self, response: Response, filename: str) -> None:
        image_path = path.join(self._images_folder, filename)
        with open(image_path, "wb") as fp:
            fp.write(response.body())

    def _download_images(self, generation: Generation) -> None:
        generation_id = generation.generation_id
        data = json.loads(generation.data)
        json_entry = dict(generation_id=generation_id, data=data, image_names=list())
        try:
            for generation_url in generation.generation_urls:
                url = generation_url.value
                response = self._make_request(url)
                url_path = urlparse(url).path
                filename = PurePosixPath(url_path).name
                filename = f"{generation.id}-{filename}"
                self._save_image(response, filename)
                json_entry["image_names"].append(filename)
                self._page.wait_for_timeout(self._download_delay)
            generation.data = json.dumps(json_entry)
            generation.status = "completed"
            self._logger.debug(f"Image downloaded, generation id: {generation_id}")
        except:  # todo retryerror tenacity
            # todo only mark as failed if http related error
            generation.status = "failed"
            self._logger.warning(
                f"Failed download of image, generation id: {generation_id}"
            )
            raise
        finally:
            self._session.commit()

    def start_scraping(self) -> None:
        self._logger.info("Starting image downloader.")
        select_stmt = select(Generation).filter_by(status="pending")
        cursor = self._session.scalars(select_stmt)
        for row in cursor:
            self._download_images(row)
