from bs4 import BeautifulSoup
from playwright.async_api import Page


class BoardGridView:
    def __init__(self, page: Page) -> None:
        self._page = page
        self._board_urls = set()

    async def extract_urls(self):
        html = await self._page.content()
        soup = BeautifulSoup(html, "lxml")

        for board in soup.select("[role=listitem] a"):
            # for board in soup.find_all("a", role="listitem"):
            self._board_urls.add(board["href"])

    async def start_view(self):
        await self.extract_urls()

    def get_board_urls(self):
        return self._board_urls
