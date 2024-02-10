import itertools
import urllib.parse
from typing import Iterator

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from src.browser import Browser
from src.db import setup_db
from src.settings import OUTPUT_DIR, PROXY_LIST_PATH
from src.views.board_grid import BoardGridView


class Scraper:
    def __init__(self, query: str) -> None:
        query = urllib.parse.quote_plus(query)
        self.initial_url = (
            f"https://www.pinterest.com/search/boards/?q={query}&rs=typed"
        )
        self.engine: Engine | None = None
        self.session: Session | None = None
        self.proxy_list: Iterator | None = None

    def load_proxy_list(self) -> list[dict]:
        proxy_list = []
        with PROXY_LIST_PATH.open("r", encoding="utf-8") as fp:
            for line in fp:
                [credentials, server] = line.split("@")
                [username, password] = credentials.split(":")
                proxy_list.append(
                    {"server": server, "username": username, "password": password}
                )

        return proxy_list

    def setup(self) -> None:
        OUTPUT_DIR.mkdir(exist_ok=True)
        self.engine = setup_db()
        self.session = Session(self.engine)
        self.proxy_list = itertools.cycle(self.load_proxy_list())

    def scrape_board_urls(self) -> set:
        with Browser(url=self.initial_url, proxy=next(self.proxy_list)) as page:
            view = BoardGridView(page=page)
            view.start_view()
            urls = view.get_board_urls()

        print(list(urls))

        return urls

    def run(self) -> None:
        try:
            self.setup()
            self.scrape_board_urls()
        finally:
            if self.session is not None:
                self.session.close()
