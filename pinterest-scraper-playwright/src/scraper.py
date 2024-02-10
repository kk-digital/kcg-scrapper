import itertools
import logging
import urllib.parse
from typing import Iterator

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from src.browser import Browser
from src.db import Url, setup_db
from src.settings import OUTPUT_DIR, PROXY_LIST_PATH
from src.views.board_grid import BoardGridView


class Scraper:
    def __init__(self, query: str) -> None:
        query = urllib.parse.quote_plus(query)
        self.initial_url = (
            f"https://www.pinterest.com/search/boards/?q={query}&rs=typed"
        )
        self.output_dir = OUTPUT_DIR
        self.proxy_list_path = PROXY_LIST_PATH
        self.engine: Engine | None = None
        self.session: Session | None = None
        self.proxy_list: Iterator | None = None
        self.logger = logging.getLogger(__name__)

    def load_proxy_list(self) -> list[dict]:
        proxy_list = []
        with self.proxy_list_path.open("r", encoding="utf-8") as fp:
            for line in fp:
                [credentials, server] = line.split("@")
                [username, password] = credentials.split(":")
                proxy_list.append(
                    {"server": server, "username": username, "password": password}
                )

        return proxy_list

    def setup(self) -> None:
        self.output_dir.mkdir(exist_ok=True)
        self.engine = setup_db()
        self.session = Session(self.engine)
        self.proxy_list = itertools.cycle(self.load_proxy_list())
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
            datefmt="%m-%d %H:%M:%S",
        )
        self.logger.info("Scraper setup complete")

    def scrape_board_urls(self) -> list[str]:
        with Browser(url=self.initial_url, proxy=next(self.proxy_list)) as page:
            self.logger.info(f"Scraping board urls from {self.initial_url}")
            view = BoardGridView(page=page)
            view.start_view()

        urls = view.get_board_urls()
        new_urls = []
        for url in urls:
            stmt = select(Url).where(Url.url == url)
            result = self.session.scalars(stmt).first()
            if result is None:
                new_urls.append(url)
        self.logger.info(f"Found {len(new_urls)} board urls")

        return new_urls

    def run(self) -> None:
        try:
            self.setup()
            self.scrape_board_urls()
        finally:
            if self.session is not None:
                self.session.close()
