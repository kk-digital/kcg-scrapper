import itertools
import logging
import urllib.parse
from typing import Iterator

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from src import settings, utils
from src.browser import Browser
from src.db import setup_db
from src.views.board_grid import BoardGridView
from src.views.pin_grid import PinGridView


class Scraper:
    def __init__(self, query: str) -> None:
        query = urllib.parse.quote_plus(query)
        self.base_url = "https://www.pinterest.com"
        self.initial_url = f"{self.base_url}/search/boards/?q={query}&rs=typed"
        self.output_dir = settings.OUTPUT_DIR
        self.proxy_list_path = settings.PROXY_LIST_PATH
        self.engine: Engine
        self.session: Session
        self.proxy_list: Iterator
        self.logger = logging.getLogger(__name__)

    def setup(self) -> None:
        self.output_dir.mkdir(exist_ok=True)
        self.engine = setup_db()
        self.session = Session(self.engine)
        self.proxy_list = itertools.cycle(utils.load_proxy_list(self.proxy_list_path))
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
            datefmt="%m-%d %H:%M:%S",
        )
        self.logger.info("Scraper setup complete")

    @utils.default_retry
    def scrape_board_urls(self) -> list[str]:
        with Browser(url=self.initial_url, proxy=next(self.proxy_list)) as page:
            self.logger.info(f"Scraping board urls from {self.initial_url}")
            view = BoardGridView(page=page)
            view.start_view()

        urls = view.get_board_urls()
        processed_urls = utils.join_urls(self.base_url, urls)
        processed_urls = utils.exclude_duplicates(processed_urls, self.session)
        self.logger.info(f"Found {len(processed_urls)} board urls")

        return processed_urls

    @utils.default_retry
    def scrape_board_pins(self, url: str) -> list[str]:
        with Browser(url=url, proxy=next(self.proxy_list)) as page:
            self.logger.info(f"Scraping board {url}")
            view = PinGridView(page=page)
            view.start_view()

        urls = view.get_pin_urls()
        processed_urls = utils.join_urls(self.base_url, urls)
        processed_urls = utils.exclude_duplicates(processed_urls, self.session)
        self.logger.info(f"Found {len(processed_urls)} pin urls for board {url}")

        return processed_urls

    def scrape_boards(self, urls: list[str]) -> None:
        with self.output_dir.joinpath("pin_urls.txt").open("a", encoding="utf-8") as fp:
            for url in urls:
                pin_urls = self.scrape_board_pins(url)
                for pin_url in pin_urls:
                    fp.write(pin_url + "\n")
                # append board url so it's not rescraped
                pin_urls.append(url)
                utils.insert_urls(pin_urls, self.session)

    def run(self) -> None:
        try:
            self.setup()
            board_urls = self.scrape_board_urls()
            self.scrape_boards(board_urls)
        finally:
            if self.session is not None:
                self.session.close()
