import logging
import re
import urllib.parse
from collections import namedtuple
from sqlite3 import Row
from typing import Callable
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from settings import MAX_RETRY
from src.classes.scroll_stage import ScrollStage
from src.pin_stage import PinStage
from src.utils import time_perf

logger = logging.getLogger(f"scraper.{__name__}")
URL = "https://www.pinterest.com/search/boards/?q={}&rs=typed"


class BoardStage(ScrollStage):
    def __init__(
        self, job: Row | dict, max_workers: int = None, headless: bool = True
    ) -> None:
        super().__init__(job, max_workers, headless)
        self.__first_wait = False

    @time_perf("scroll to end of boards page")
    def _scroll_and_scrape(self, fn: Callable, check_more_like_this=True) -> None:
        return super()._scroll_and_scrape(fn, check_more_like_this)

    def _scrape_data(self, boards_data: list) -> None:
        board_selector = "div[role=listitem] a"

        if not self.__first_wait:
            self._wait.until(
                ec.presence_of_element_located((By.CSS_SELECTOR, board_selector))
            )
            self.__first_wait = True

        soup = BeautifulSoup(self._driver.page_source, "lxml")
        boards = soup.select(board_selector)

        data = []
        for board in boards:
            url = board["href"]
            title = board.select_one("[title]").string
            pin_count = board.select_one(".O2T.swG").get_text()
            pin_count = int(re.search(r"\d+", pin_count).group())
            BoardData = namedtuple("BoardData", ["url", "title", "pin_count"])
            data.append(BoardData(url, title, pin_count))
        boards_data += data

    def _scrape(self) -> None:
        boards_data = []

        self._scroll_and_scrape(
            lambda: self._scrape_data(boards_data), check_more_like_this=False
        )

        rows = [
            (
                self._job["id"],
                urljoin(self._driver.current_url, data.url),
                data.title,
                data.pin_count,
            )
            for data in boards_data
        ]
        logger.info(f'Found {len(rows)} boards for {self._job["query"]}.')
        self._db.create_many_board(rows)

    def start_scraping(self, execute_next_stage: bool = True) -> None:
        super().start_scraping()

        query = urllib.parse.quote_plus(self._job["query"])
        url = URL.format(query)

        for i in range(MAX_RETRY + 1):
            try:
                self._driver.get(url)
                self._scrape()
                break
            except TimeoutException:
                if i == MAX_RETRY:
                    self.close()
                    raise

                logger.exception(f"Timeout scraping boards from {url}, retrying...")
            except:
                self.close()
                raise

        self.close()
        self._db.update_job_stage(self._job["id"], "pin")
        logger.info("Finished scraping of boards. Starting pins stage.")

        if not execute_next_stage:
            return

        PinStage(
            job=self._job, max_workers=self._max_workers, headless=self._headless
        ).start_scraping()
