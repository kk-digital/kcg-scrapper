import json
import logging
import os
from os import path
from pathlib import PurePosixPath

from playwright.sync_api import Page, Response
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from sqlalchemy import select
from tenacity import stop_after_attempt, wait_fixed, Retrying, retry_if_exception_type

import settings
from src.db import engine as db_engine

from src.db.model import Generation, GenerationUrl
from urllib.parse import urlparse

from src.exceptions import PlaywrightHTTTPError


class ImageDownloader:
    def __init__(self, page: Page) -> None:
        engine = db_engine.get_engine()
        self._session = db_engine.get_session(engine)
        self._logger = logging.getLogger(f"scraper.{__name__}")
        self._page = page
        self._download_delay = settings.DOWNLOAD_DELAY
        self._max_retry = settings.MAX_RETRY
        # init images folder
        self._images_folder = settings.IMAGES_FOLDER
        os.makedirs(self._images_folder, exist_ok=True)

    def _make_request(self, url: str) -> Response:
        with self._page.expect_response(url) as response_info:
            self._page.goto(url)
        response = response_info.value
        code = response.status
        if code != 200:
            raise PlaywrightHTTTPError(f"Got non 200 status code loading {url}.")

        return response

    def _save_image(self, response: Response, filename: str) -> None:
        image_path = path.join(self._images_folder, filename)
        with open(image_path, "wb") as fp:
            fp.write(response.body())

    def _download_image(self, generation_url: GenerationUrl, filenames: list) -> None:
        url = generation_url.value
        response = self._make_request(url)
        url_path = urlparse(url).path
        filename = PurePosixPath(url_path).name
        filename = f"{generation_url.generation.generation_id}-{filename}"
        self._save_image(response, filename)
        filenames.append(filename)
        self._page.wait_for_timeout(self._download_delay)

    def _process_generation(self, generation: Generation) -> None:
        generation_id = generation.generation_id
        data = json.loads(generation.data)
        json_entry = dict(generation_id=generation_id, data=data, filenames=list())
        try:
            for generation_url in generation.generation_urls:
                retryer = Retrying(
                    reraise=True,
                    stop=stop_after_attempt(self._max_retry),
                    wait=wait_fixed(self._download_delay),
                    retry=retry_if_exception_type(
                        (PlaywrightHTTTPError, PlaywrightTimeoutError)
                    ),
                )
                retryer(self._download_image, generation_url, json_entry["filenames"])

            generation.data = json.dumps(json_entry)
            generation.status = "completed"
            self._logger.info(f"Image downloaded, generation id: {generation_id}")
        except PlaywrightHTTTPError:
            generation.status = "failed"
            self._logger.warning(
                f"Got non 200 status code at download of image, generation id: {generation_id}"
            )
        except Exception as e:
            # if response body is larger than 10mb an implicit playwright error occurs
            if "was evicted" in e.args[0]:
                generation.status = "failed"
                return

            self._logger.error(
                f"Got unexpected error at download of image, generation id: {generation_id}"
            )
            raise
        finally:
            self._session.commit()

    def start_scraping(self) -> None:
        self._logger.info("Starting image downloader.")
        select_stmt = select(Generation).filter_by(status="pending")
        cursor = self._session.scalars(select_stmt)
        for generation in cursor:
            self._process_generation(generation)
        self._logger.info("End of image download stage.")
