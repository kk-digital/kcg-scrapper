from playwright.async_api import Page
from scrapy.settings import Settings


class LoginView:
    def __init__(self, page: Page, settings: Settings):
        self._page = page
        self._storage_state_file = str(settings.get("STORAGE_STATE_FILE"))
        self._google_username = settings["GOOGLE_USERNAME"]
        self._google_password = settings["GOOGLE_PASSWORD"]

    async def start_view(self):
        await self._page.get_by_role("button", name="Google").click()

        await self._page.get_by_label("Email or phone").type(
            self._google_username, delay=100
        )
        await self._page.get_by_role("button", name="Next").click()

        await self._page.get_by_label("Enter your password").type(
            self._google_password, delay=100
        )
        await self._page.get_by_role("button", name="Next").click()

        await self._page.wait_for_timeout(10000)
        await self._save_storage_state()

    async def _save_storage_state(self):
        await self._page.context.storage_state(path=self._storage_state_file)
