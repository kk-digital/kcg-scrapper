import logging
import os

import fire

if os.getenv("PYTHON_ENV", "development") == "development":
    from dotenv import load_dotenv

    load_dotenv()

from src.utils import Utils

from src.scraper import Scraper


class Command:
    def __init__(self):
        self._logger = logging.getLogger(f"scraper.{__name__}")
        Scraper.init_config()
        self._utils = Utils()

    def start_scraping(
        self,
        prompt_filter_list: str | None = None,
        use_storage_state: bool = False,
        disable_showcase_scrolling: bool = False,
    ) -> None:
        prompt_filters = None
        if prompt_filter_list:
            prompt_filters = self._utils.read_filters(prompt_filter_list)

        scraper = Scraper()
        scraper.start_scraping(
            prompt_filters=prompt_filters,
            use_storage_state=use_storage_state,
            disable_showcase_scrolling=disable_showcase_scrolling,
        )

    def export_json_data(
        self, prompt_filter: str | None = None, test_export: bool = False
    ) -> None:
        self._utils.export_json_data(prompt_filter, test_export)

    def compress_output(self, test_export: bool = False) -> None:
        self._utils.compress_output(test_export)


if __name__ == "__main__":
    fire.Fire(Command)
