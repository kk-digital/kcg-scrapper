import logging
import os
import shutil
import time
import uuid
from datetime import datetime
from os import path
from sqlite3 import Row
from typing import List, Optional
from urllib.parse import urlparse, urlunparse

import jsonlines
from requests import Session, RequestException, Response
from selenium.common import TimeoutException

from pinterest_scraper.stage import Stage
from settings import MAX_RETRY, OUTPUT_FOlDER, TIMEOUT, DOWNLOAD_DELAY, MAX_OUTPUT_SIZE

logger = logging.getLogger(f"scraper.{__name__}")


class DownloadStage(Stage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__session: Optional[Session] = None
        self.__json_fh: Optional[jsonlines.Writer] = None
        self.__output_size = None

    def __init_output_dir(self) -> None:
        dir_path = path.join(OUTPUT_FOlDER, "jobs", self._job["query"])
        self.__output_path = dir_path
        self.__images_path = path.join(dir_path, "images")
        self.__html_path = path.join(dir_path, "html")
        os.makedirs(self.__images_path, exist_ok=True)
        os.makedirs(self.__html_path, exist_ok=True)

    def __init_output_size(self) -> None:
        size = 0
        for dir_path, dir_names, file_names in os.walk(self.__output_path):
            for basename in file_names:
                size += path.getsize(path.join(dir_path, basename))

        self.__output_size = size

    def __get_img_urls(self, url: str) -> List[str]:
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split("/")
        path_parts[1] = "originals"

        extensions = ["jpg", "png"]
        new_urls = []
        for ext in extensions:
            filename = path.splitext(path_parts[-1])[0]
            basename = f"{filename}.{ext}"
            path_parts[-1] = basename
            new_path = "/".join(path_parts)
            new_url = urlunparse(
                (
                    parsed_url.scheme,
                    parsed_url.netloc,
                    new_path,
                    parsed_url.params,
                    parsed_url.query,
                    parsed_url.fragment,
                )
            )
            new_urls.append(new_url)

        return new_urls

    def __save_img(self, res: Response, img_url: str, pin_uuid: uuid.UUID) -> str:
        ext = path.splitext(img_url)[1]
        basename = f"{pin_uuid}{ext}"
        img_path = path.join(self.__images_path, basename)

        with open(img_path, "wb") as fh:
            fh.write(res.content)

        self.__output_size += path.getsize(img_path)

        return basename

    def __download_pin_img(self, pin: Row, pin_uuid: uuid.UUID) -> str:
        img_urls = self.__get_img_urls(pin["img_url"])
        for img_url in img_urls:
            res = self.__session.get(img_url, timeout=TIMEOUT)

            # if xml, have to try with the other url
            if res.headers["content-type"] == "application/xml":
                continue

            res.raise_for_status()

            img_name = self.__save_img(res, img_url, pin_uuid)

            break

        # noinspection PyUnboundLocalVariable
        return img_name

    def __save_pin_html(self, pin: Row, pin_uuid: uuid.UUID) -> None:
        self._driver.get(pin["url"])

        file_path = path.join(self.__html_path, f"{pin_uuid}.html")
        with open(file_path, "w", encoding="utf-8") as fh:
            fh.write(self._driver.page_source)

        self.__output_size += path.getsize(file_path)

    def __add_to_json(self, pin_uuid: uuid.UUID, img_name: str) -> None:
        if not self.__json_fh:
            self.__json_fh = jsonlines.open(
                path.join(self.__output_path, "pins.jsonl"), "a"
            )

        self.__json_fh.write(
            dict(
                query=self._job["query"],
                img_name=img_name,
                html_name=f"{pin_uuid}.html",
            )
        )

    def __check_output_size(self, ignore_check: bool = False) -> None:
        exceed_size = self.__output_size >= MAX_OUTPUT_SIZE
        if not exceed_size and not ignore_check:
            return

        self.__json_fh.close()
        self.__json_fh = None

        filename = f'{datetime.now().timestamp()}-{self._job["query"]}'
        archive_path = path.join(OUTPUT_FOlDER, filename)
        shutil.make_archive(archive_path, "zip", self.__output_path)
        shutil.rmtree(self.__output_path)
        self.__init_output_dir()
        self.__output_size = 0

    def start_scraping(self) -> None:
        super().start_scraping()
        self.__init_output_dir()
        self.__init_output_size()

        self.__session = Session()
        retries = 0
        while True:
            try:
                # retrieve pins here to not re-download pins
                # successfully scraped before error
                pins = self._db.get_all_board_or_pin_by_job_id("pin", self._job["id"])
                for pin in pins:
                    pin_uuid = uuid.uuid1()
                    img_name = self.__download_pin_img(pin, pin_uuid)
                    self.__save_pin_html(pin, pin_uuid)
                    self.__add_to_json(pin_uuid, img_name)
                    self.__check_output_size()

                    self._db.update_board_or_pin_done_by_url("pin", pin["url"], 1)
                    retries = 0
                    logger.info(f"Successfully scraped pin {pin['url']}.")
                    time.sleep(DOWNLOAD_DELAY)

                self.__check_output_size(True)

                break
            except (RequestException, TimeoutException):
                if retries == MAX_RETRY:
                    self.__json_fh.close()
                    self.__session.close()
                    raise

                # noinspection PyUnboundLocalVariable
                logger.exception(
                    f"Exception downloading pin: {pin['url']}, retrying..."
                )
                retries += 1

        self._db.update_job_stage(self._job["id"], "completed")
        logger.info(f"Finished scraping of job for query {self._job['query']}.")
