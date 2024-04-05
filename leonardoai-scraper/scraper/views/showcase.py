import logging

from playwright.async_api import JSHandle, Page, Request
from scrapy.settings import Settings


class ShowcaseView:
    def __init__(self, page: Page, settings: Settings):
        self._page = page
        self._scroll_times = settings["SCROLL_TIMES"]
        self._scroll_delay = settings["SCROLL_DELAY"]
        self._generations = []
        self._logger = logging.getLogger(__name__)
        self.current_category = None

    async def _request_handler(self, request: Request):
        if not (
            request.method == "POST"
            and "graphql" in request.url
            and request.post_data_json["operationName"] == "GetFeedImages"
        ):
            return

        response = await request.response()
        data = await response.json()
        data = data["data"]["generated_images"]
        for gen in data:
            gen["category"] = self.current_category
        self._generations.extend(data)
        self._logger.info(f"Got {len(data)} generations")

    async def _start_scrolling(self):
        self._logger.debug("Start scrolling")
        document_element: JSHandle = await self._page.evaluate_handle(
            "document.documentElement"
        )

        async def get_scroll_height():
            scroll_height_property = await document_element.get_property("scrollHeight")
            return await scroll_height_property.json_value()

        last_scroll_height = await get_scroll_height()

        for _ in range(self._scroll_times):
            await self._page.evaluate(f"window.scrollTo(0, {last_scroll_height})")
            await self._page.wait_for_timeout(self._scroll_delay)
            last_scroll_height = await get_scroll_height()
            self._logger.debug("Scrolling")

    async def start_view(self):
        await self._page.wait_for_load_state()
        # start intercepting requests
        self._page.on("requestfinished", self._request_handler)

        categories = ["Trending", "Anime", "Sci-Fi", "Character", "Architecture"]
        for category in categories:
            await self._page.get_by_role("button", name=category).click()
            self.current_category = category
            if category == "Trending":
                await self._page.get_by_role("menuitem", name="New").click()

            await self._page.wait_for_timeout(3000)
            self._logger.info(f"{category} generations section loaded")
            await self._start_scrolling()
            await self._page.wait_for_timeout(3000)

        self._logger.debug("Finished showcase view")
        return self._generations
