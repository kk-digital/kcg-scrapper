from bs4 import BeautifulSoup

from scraper.views._base_view import BaseView


class BoardGridView(BaseView):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._board_urls = set()

    async def _extract_urls(self):
        html = await self._page.content()
        soup = BeautifulSoup(html, "lxml")

        for board in soup.select("[role=listitem] a"):
            self._board_urls.add(board["href"])

    async def start_view(self):
        await self._page.wait_for_timeout(self._short_wait)
        await self._scroll_to_bottom_while_do(self._extract_urls)

    def get_board_urls(self):
        return self._board_urls
