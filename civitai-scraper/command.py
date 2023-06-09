import json
import os
import shutil
import zipfile
from os import path

import fire
import jsonlines

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

    def compress_output(self) -> None:
        print("Compressing, please wait.")
        # first convert jsonl to json
        jsonl_path = path.join(settings.FILES_STORE, "data.jsonl")
        json_list = []
        with jsonlines.open(jsonl_path, "r") as fp:
            for item in fp:
                json_list.append(item)
        os.remove(jsonl_path)

        with open(jsonl_path.replace("jsonl", "json"), "w") as fp:
            json.dump(json_list, fp)

        # compression
        # compress in MAX_SIZE parts
        zip_count = 1
        zip_file = None
        file_list = os.listdir(settings.FILES_STORE)
        file_list.remove("data.json")
        for filename in file_list:
            if not zip_file:
                zip_count_str = str(zip_count).zfill(6)
                zip_file_path = path.join(settings.FILES_STORE, f"{zip_count_str}.zip")
                zip_file = zipfile.ZipFile(zip_file_path, "w")
                zip_count += 1

            path_to_file = path.join(settings.FILES_STORE, filename)
            zip_file.write(path_to_file, arcname=filename)
            os.remove(path_to_file)

            # noinspection PyUnboundLocalVariable
            current_size = path.getsize(zip_file_path)
            if current_size >= settings.MAX_ARCHIVE_SIZE:
                zip_file.close()
                zip_file = None

        if zip_file:
            zip_file.close()
        # compress json and parts in single zip
        zip_file_path = path.join(settings.FILES_STORE, "output.zip")
        final_zip_file = zipfile.ZipFile(zip_file_path, "w")
        file_list = os.listdir(settings.FILES_STORE)
        file_list.remove("output.zip")
        for filename in file_list:
            path_to_file = path.join(settings.FILES_STORE, filename)
            final_zip_file.write(path_to_file, arcname=filename)
            os.remove(path_to_file)

        final_zip_file.close()

        print("Done.")


fire.Fire(Command)
