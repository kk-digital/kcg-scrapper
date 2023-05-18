import json
import logging
import os
import queue
import re
import shutil
import time
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from os import path
from queue import SimpleQueue
from sqlite3 import Row
from typing import List, Optional
from urllib.parse import urlparse, urlunparse

from requests import RequestException, Response, Session
from selenium.common import TimeoutException

import settings
from src.classes.base_stage import BaseStage

logger = logging.getLogger(f"scraper.{__name__}")


class DownloadStage(BaseStage):
    def __init__(self, json_entries: SimpleQueue = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__json_entries = json_entries
        self.__session: Optional[Session] = None

    def __init_output_dir(self, make_dirs: bool = False) -> None:
        dir_path = path.join(settings.OUTPUT_FOlDER, "jobs", self._job["query"])
        self.__output_path = dir_path
        self.__images_path = path.join(dir_path, "images")
        self.__html_path = path.join(dir_path, "html")
        self.__json_path = path.join(dir_path, "db.json")

        if make_dirs:
            os.makedirs(self.__images_path, exist_ok=True)
            os.makedirs(self.__html_path, exist_ok=True)

    def __get_img_urls(self, url: str) -> List[str]:
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split("/")
        path_parts[1] = "originals"

        extensions = ["jpg", "png", "gif"]
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

        return basename

    def __download_pin_img(self, pin: Row, pin_uuid: uuid.UUID) -> str:
        img_urls = self.__get_img_urls(pin["img_url"])
        for img_url in img_urls:
            res = self.__session.get(img_url, timeout=settings.TIMEOUT)

            # if xml, have to try with the other url
            if res.headers["content-type"] == "application/xml":
                continue

            res.raise_for_status()

            img_name = self.__save_img(res, img_url, pin_uuid)

            break

        # noinspection PyUnboundLocalVariable
        return img_name

    def __save_pin_html(self, url: str, pin_uuid: uuid.UUID) -> None:
        self._driver.get(url)

        file_path = path.join(self.__html_path, f"{pin_uuid}.html")
        with open(file_path, "w", encoding="utf-8") as fh:
            source_code = self._driver.page_source
            source_code = re.sub(
                "<script.*?>.*?</script>|<style.*?>.*?</style>",
                "",
                source_code,
                flags=re.DOTALL,
            )
            fh.write(source_code)

    def __add_to_json(self, pin_uuid: uuid.UUID, img_name: str, pin_url: str) -> None:
        self.__json_entries.put_nowait(
            dict(
                pin_url=pin_url,
                query=self._job["query"],
                img_name=img_name,
                html_name=f"{pin_uuid}.html",
            )
        )

    def __start_scraping(self, pin_queue: SimpleQueue) -> None:
        self.__init_output_dir()
        self.__session = Session()

        pin = pin_queue.get_nowait()
        retries = 0
        while pin:
            if self._stop_event.is_set():
                break

            try:
                super().start_scraping()
                pin_url = pin["url"]
                pin_uuid = uuid.uuid1()
                self.__save_pin_html(pin_url, pin_uuid)
                img_name = self.__download_pin_img(pin, pin_uuid)
                self.__add_to_json(pin_uuid, img_name, pin_url)
                self._db.update_board_or_pin_done_by_url("pin", pin["url"], 1)
                logger.info(f"Successfully scraped pin {pin['url']}.")
                retries = 0
                pin = pin_queue.get_nowait()
                time.sleep(settings.DOWNLOAD_DELAY)

            except queue.Empty:
                self.close()
                self.__session.close()
                break
            except (RequestException, TimeoutException):
                if retries == settings.MAX_RETRY:
                    self.__session.close()
                    self._stop_event.set()
                    raise

                logger.exception(
                    f"Exception downloading pin: {pin['url']}, retrying..."
                )
                retries += 1
            except:
                self.__session.close()
                self._stop_event.set()
                logger.exception(
                    f"Unhandled exception downloading pin: {pin['url']}, retrying..."
                )
                raise

    def __archive_output(self) -> None:
        zip_count = 1
        zip_name = "{}-{}.zip"
        create_new_zip = True
        zipf = None
        zip_path = None

        for file in os.listdir(self.__images_path):
            if create_new_zip:
                new_zip_name = zip_name.format(
                    self._job["query"], str(zip_count).zfill(6)
                )
                zip_path = path.join(self.__output_path, new_zip_name)
                zipf = zipfile.ZipFile(file=zip_path, mode="w")
                create_new_zip = False

            filename = path.splitext(file)[0]
            html_basename = f"{filename}.html"
            zipf.write(
                filename=path.join(self.__images_path, file), arcname=f"images/{file}"
            )
            zipf.write(
                filename=path.join(self.__html_path, html_basename),
                arcname=f"html/{html_basename}",
            )

            exceed_size = path.getsize(zip_path) >= settings.MAX_OUTPUT_SIZE
            if not exceed_size:
                continue

            zipf.close()
            zip_count += 1
            create_new_zip = True

        zipf.close()
        shutil.rmtree(self.__images_path)
        shutil.rmtree(self.__html_path)

    def start_scraping(self) -> None:
        self.__init_output_dir(make_dirs=True)
        json_entries = SimpleQueue()

        pins = self._db.get_all_board_or_pin_by_job_id("pin", self._job["id"])
        pins_queue = SimpleQueue()
        for board in pins:
            pins_queue.put_nowait(board)
        del pins

        with ThreadPoolExecutor(self._max_workers) as executor:
            futures = []
            for _ in range(self._max_workers):
                task = lambda: self.__class__(
                    job=self._job, headless=self._headless, json_entries=json_entries
                ).__start_scraping(pin_queue=pins_queue)

                futures.append(executor.submit(task))

        logger.debug("Writing json.")
        if json_entries.qsize() > 0:
            entries = []
            while not json_entries.empty():
                entries.append(json_entries.get_nowait())

            if path.exists(self.__json_path):
                with open(self.__json_path, "r", encoding="utf-8") as fh:
                    entries += json.load(fh)

            with open(self.__json_path, "w", encoding="utf-8") as fh:
                json.dump(entries, fh)

            del entries

        for future in futures:
            try:
                future.result()
            except queue.Empty:
                pass

        logger.debug("Archiving output.")
        self.__archive_output()

        self._db.update_job_stage(self._job["id"], "completed")
        logger.info(f"Finished scraping of job for query {self._job['query']}.")
