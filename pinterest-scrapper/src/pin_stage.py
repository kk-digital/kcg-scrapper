import logging
import queue
from concurrent.futures import ThreadPoolExecutor
from queue import SimpleQueue
from typing import Callable
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium.common import (
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchElementException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

import settings
from src.classes.scroll_stage import ScrollStage
from src.download_stage import DownloadStage
from src.utils import time_perf

logger = logging.getLogger(f"scraper.{__name__}")


class PinStage(ScrollStage):
    @time_perf("scroll to end of board and get all pins")
    def _scroll_and_scrape(self, fn: Callable, check_more_like_this=False) -> None:
        super()._scroll_and_scrape(fn, check_more_like_this)

    def _scrape_urls(self, urls: set) -> None:
        pin_selector = 'div.wsz.zmN > div[data-test-id="deeplink-wrapper"] a'

        try:
            self._wait.until(
                ec.presence_of_element_located((By.CSS_SELECTOR, pin_selector))
            )
        # there is boards that has no pins, just sections
        except TimeoutException:
            return

        soup = BeautifulSoup(self._driver.page_source, "lxml")
        pins = soup.select(pin_selector)

        for pin in pins:
            try:
                pin_url = pin["href"]
                pin_img_url = pin.select_one("img")["src"]
                pin_data = (pin_url, pin_img_url)
                urls.add(pin_data)
            # catch type error in case try to access non-existing attr on bs4 tag
            except TypeError:
                continue

    def _scrape(self) -> None:
        pin_urls = set()

        section_selector = "div[data-test-id=board-section]"
        wait_section_to_be_clickable = lambda: self._wait.until(
            ec.element_to_be_clickable((By.CSS_SELECTOR, section_selector))
        )
        get_sections = lambda: self._wait.until(
            ec.presence_of_all_elements_located((By.CSS_SELECTOR, section_selector))
        )

        try:
            # there may be sections or not
            # no need to scroll since all sections are in dom at first
            wait_section_to_be_clickable()
            sections = get_sections()
        except TimeoutException:
            pass
        else:
            # not inside try block to not catch timeout exceptions from subsequent code
            n_sections = len(sections)
            section_n = 0
            while True:
                try:
                    # re-selecting since on every section click els are removed
                    wait_section_to_be_clickable()
                    sections = get_sections()
                    sections[section_n].click()

                    self._scroll_and_scrape(
                        lambda: self._scrape_urls(pin_urls), check_more_like_this=True
                    )
                    self._driver.back()

                    section_n += 1
                    if section_n == n_sections:
                        break
                # test if sign up float window intercepted the click
                # and close it
                except ElementClickInterceptedException as e:
                    try:
                        sign_up_close_el = self._driver.find_element(
                            By.CSS_SELECTOR, ".p6V .qrs"
                        )
                        sign_up_close_el.click()
                    except NoSuchElementException:
                        raise e

        # time to get the pins that are in main page
        self._scroll_and_scrape(
            lambda: self._scrape_urls(pin_urls), check_more_like_this=True
        )

        pin_urls = list(pin_urls)

        rows = [
            (self._job["id"], urljoin(self._driver.current_url, urls[0]), urls[1])
            for urls in pin_urls
        ]
        logger.info(
            f'Found {len(rows)} pins for board {self._driver.current_url}, query: {self._job["query"]}.'
        )
        self._db.create_many_pin(rows)

    def __start_scraping(self, board_queue: SimpleQueue) -> None:
        board = board_queue.get_nowait()
        retries = 0
        while board:
            if self._stop_event.is_set():
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
                if retries == settings.MAX_RETRY:
                    self.close()
                    self._stop_event.set()
                    raise

                logger.exception(
                    f"Timeout scraping pins from {board['url']}, retrying..."
                )
                retries += 1
            except:
                self.close()
                self._stop_event.set()
                logger.exception(
                    f"Unhandled exception scraping pins from {board['url']}, retrying..."
                )
                raise

    def start_scraping(self) -> None:
        boards = self._db.get_all_board_or_pin_by_job_id("board", self._job["id"])
        board_queue = SimpleQueue()
        for board in boards:
            board_queue.put_nowait(board)
        del boards

        with ThreadPoolExecutor(self._max_workers) as executor:
            futures = []
            for _ in range(self._max_workers):
                task = lambda: self.__class__(
                    job=self._job, headless=self._headless
                ).__start_scraping(board_queue=board_queue)

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
