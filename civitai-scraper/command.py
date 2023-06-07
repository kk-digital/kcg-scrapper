import os
import shutil
from os import path

import fire

import settings
from src.api_scraping import Scraper


class Command:
    def start_scraping(self) -> None:
        print("Starting operations.")
        Scraper().start_scraping()
        print("End operations.")

    def delete_output(self) -> None:
        while True:
            confirm = input(
                "⚠️This action delete the db and the entire output folder. Do you want to continue? (y/n): "
            )
            if confirm == "y":
                break
            elif confirm == "n":
                return

        # remove output folder
        shutil.rmtree(settings.FILES_STORE, ignore_errors=True)
        # remove db
        if path.isfile(settings.SQLITE_NAME):
            os.remove(settings.SQLITE_NAME)

        print("Done.")


fire.Fire(Command)
