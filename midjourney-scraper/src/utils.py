import itertools
import json
import logging
import os
import zipfile
from os import path
from typing import Optional

import settings
from sqlalchemy import select
from src.db import engine as db_engine
from src.db.model import Generation


class Utils:
    def __init__(self) -> None:
        engine = db_engine.get_engine()
        self._session = db_engine.get_new_session(engine)
        self._logger = logging.getLogger(f"scraper.{__name__}")
        self._output_folder = settings.OUTPUT_FOLDER
        self._images_folder = settings.IMAGES_FOLDER
        self._json_path = settings.EXPORT_JSON_PATH
        self._zip_path = settings.ARCHIVE_PATH
        self._max_archive_size = settings.MAX_ARCHIVE_SIZE

    def export_json_data(
        self, prompt_filter: Optional[str], test_export: bool, confirmation: bool = True
    ) -> None:
        self._logger.info("Starting exports.")

        if confirmation:
            print(
                'This action overrides the json db already present if any. Type "yes" to continue.'
            )
            answer = input(">> ")
            if answer != "yes":
                return

        select_stmt = select(Generation)
        if prompt_filter:
            select_stmt = select_stmt.filter_by(
                status="completed", prompt_filter=prompt_filter
            )
        else:
            select_stmt = select_stmt.filter_by(prompt_filter=None)

        cursor = self._session.scalars(select_stmt)
        num_exports = 0
        exports_list = list()

        for generation in cursor:
            exports_list.append(json.loads(generation.data))
            if not test_export:
                self._session.delete(generation)
            num_exports += 1

        if not num_exports:
            print("No generations found.")
            return

        with open(self._json_path, "w", encoding="utf-8") as fp:
            json.dump(exports_list, fp)

        self._session.commit()
        print(f"Exported {num_exports} exports.")

    def compress_output(self, test_export: bool) -> None:
        print("Starting compression.")

        zip_count = 0
        with open(self._json_path, "r", encoding="utf-8") as fp:
            json_data = json.load(fp)
        file_list = [entry["filenames"] for entry in json_data]
        file_list = list(itertools.chain.from_iterable(file_list))

        zip_name = None
        zip_file = None
        for filename in file_list:
            if zip_file is None:
                zip_count_str = str(zip_count).zfill(6)
                zip_name = f"{self._zip_path}-{zip_count_str}.zip"
                zip_file = zipfile.ZipFile(zip_name, mode="w")

            file_path = path.join(self._images_folder, filename)
            zip_file.write(file_path, arcname=filename)

            exceeds = path.getsize(zip_name) >= self._max_archive_size
            if exceeds:
                zip_file.close()
                zip_file = None
                zip_count += 1

        if zip_file:
            zip_file.close()

        if not test_export:
            for filename in file_list:
                file_path = path.join(self._images_folder, filename)
                try:
                    os.remove(file_path)
                except FileNotFoundError:
                    pass

        print("Finished compression.")

    def read_filters(self, filters_path: str) -> list[str]:
        with open(filters_path, "r", encoding="utf-8") as fp:
            filters = [line.strip() for line in fp]

        return filters
