import logging

from playwright.async_api import Page, JSHandle, Request
from scrapy.settings import Settings


class ShowcaseView:
    def __init__(self, page: Page, settings: Settings):
        self._page = page
        self._scroll_times = settings["SCROLL_TIMES"]
        self._scroll_delay = settings["SCROLL_DELAY"]
        self._generations_data_dir = settings["GENERATIONS_DATA_DIR"]
        self._generations = []
        self._logger = logging.getLogger(__name__)

    # now return generations to export
    # def _insert_generations(self):
    #     filename = (
    #         self.generations_data_dir / f"generations-{math.trunc(time.time())}.json"
    #     )
    #     with open(filename, "w", encoding="utf-8") as fp:
    #         json.dump(self.data_to_inset, fp)
    #     self._logger.info(
    #         f"Inserted {len(self.data_to_inset)} generations to {filename}"
    #     )

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
        self._generations.extend(data)
        self._logger.debug(f"Got {len(data)} generations")

    async def start_view(self):
        await self._page.wait_for_load_state()
        await self._page.locator("a").filter(has_text="Community Feed").click()
        await self._page.wait_for_load_state()
        # start intercepting requests
        self._page.on("requestfinished", self._request_handler)

        await self._page.get_by_role("button", name="New").click()
        # let the ui load new category generations
        await self._page.wait_for_timeout(3000)
        self._logger.debug("Got to new generations section")

        await self._start_scrolling()
        # give time to intercept all requests
        await self._page.wait_for_timeout(3000)
        # self._insert_generations()
        self._logger.debug("Finished showcase view")
        return self._generations
