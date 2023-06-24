import logging

from playwright.sync_api import sync_playwright


class Scraper:
    def __init__(self) -> None:
        self.logger = logging.getLogger(f"debugger.{__name__}")

    def start_scraping(self) -> None:
        self.logger.info("Starting operations.")
        with sync_playwright() as playwright:
            browser = playwright.firefox.launch(headless=False)
            context = browser.new_context()
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            page = context.new_page()
            page.goto("https://www.midjourney.com")
            page.get_by_role("button", name="Sign In").first.click()
            print(page.title())
            page.pause()
            context.close()
            browser.close()
