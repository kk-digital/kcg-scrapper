import logging
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from queue import SimpleQueue
from typing import Callable
from urllib.parse import urljoin

from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

# from pinterest_scraper.classes.scroll_stage import ScrollStage
from src.classes.scroll_stage import ScrollStage
from src.download_stage import DownloadStage
from src.utils import time_perf
from settings import MAX_RETRY

logger = logging.getLogger(f"scraper.{__name__}")


class PinStage(ScrollStage):
    @time_perf("scroll to end of board and get all pins")
    def _scroll_and_scrape(self, fn: Callable) -> None:
        super()._scroll_and_scrape(fn)

    def _scrape_urls(self, urls: set) -> None:
        pin_selector = '.qDf > .Hsu .Hsu > .a3i div.wsz.zmN > div[data-test-id="deeplink-wrapper"] a'
        pins = self._wait.until(
            ec.presence_of_all_elements_located((By.CSS_SELECTOR, pin_selector))
        )
        for pin in pins:
            pin_url = pin.get_attribute("href")
            pin_img = pin.find_element(By.TAG_NAME, "img")
            pin_img_url = pin_img.get_attribute("src")
            pin_data = (pin_url, pin_img_url)
            urls.add(pin_data)

    def _scrape(self) -> None:
        pin_urls = set()

        get_sections = lambda: self._wait.until(
            ec.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div[data-test-id=board-section]")
            )
        )

        try:
            # there may be sections or not
            # there is no need to scroll since all sections are in dom at first
            sections = get_sections()
        except TimeoutException:
            pass
        else:
            n_sections = len(sections)
            for section_n in range(n_sections):
                # re-selecting since on every section click els are removed
                sections = get_sections()
                sections[section_n].click()
                self._scroll_and_scrape(lambda: self._scrape_urls(pin_urls))
                self._driver.back()

        # time to get the pins that are in main page
        self._scroll_and_scrape(lambda: self._scrape_urls(pin_urls))

        pin_urls = list(pin_urls)

        rows = [
            (self._job["id"], urljoin(self._driver.current_url, urls[0]), urls[1])
            for urls in pin_urls
        ]
        logger.info(
            f'Found {len(rows)} pins for board {self._driver.current_url}, query: {self._job["query"]}.'
        )
        self._db.create_many_pin(rows)

    def __start_scraping(
        self, board_queue: SimpleQueue, stop_event: threading.Event
    ) -> None:
        board = board_queue.get_nowait()
        retries = 0
        while board:
            if stop_event.is_set():
                break

            try:
                super().start_scraping()
                url = board["url"]
                self._driver.get(url)
                self._scrape()
                self._db.update_board_or_pin_done_by_url("board", url, 1)
                logger.info(f"Successfully scraped board {url}.")
                retries = 0
                board = board_queue.get_nowait()

            except queue.Empty:
                self.close()
                break
            except TimeoutException:
                if retries == MAX_RETRY:
                    self.close()
                    stop_event.set()
                    raise

                logger.exception(
                    f"Timeout scraping boards from {board['url']}, retrying..."
                )
                retries += 1
            except:
                self.close()
                stop_event.set()
                raise

    def start_scraping(self) -> None:
        boards = self._db.get_all_board_or_pin_by_job_id("board", self._job["id"])
        board_queue = SimpleQueue()
        for board in boards:
            board_queue.put_nowait(board)
        del boards

        stop_event = threading.Event()

        with ThreadPoolExecutor(self._max_workers) as executor:
            futures = []
            for _ in range(self._max_workers):
                task = lambda: self.__class__(
                    job=self._job, headless=self._headless
                ).__start_scraping(board_queue=board_queue, stop_event=stop_event)

                futures.append(executor.submit(task))

        for future in futures:
            try:
                future.result()
            except queue.Empty:
                pass

        self._db.update_job_stage(self._job["id"], "download")
        logger.info("Finished scraping of pins, starting download stage.")
        DownloadStage(
            job=self._job, max_workers=self._max_workers, headless=self._headless
        ).start_scraping()
