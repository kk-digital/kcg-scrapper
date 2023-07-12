import json
import logging
import os
import shutil
import zipfile
from os import path

from sqlalchemy import select

import settings
from src.db.model import Generation
from src.db import engine as db_engine


class Utils:
    def __init__(self) -> None:
        engine = db_engine.get_engine()
        self._session = db_engine.get_session(engine)
        self._logger = logging.getLogger(f"scraper.{__name__}")
        self._output_folder = settings.OUTPUT_FOLDER
        self._images_folder = settings.IMAGES_FOLDER
        self._json_path = path.join(self._output_folder, "images-data.json")
        self._zip_path = path.join(self._output_folder, "compressed-output")
        self._max_archive_size = settings.MAX_ARCHIVE_SIZE

    def export_json_data(self) -> None:
        self._logger.info("Starting exports.")
        print(
            'This action overrides the json db already present if any. Type "yes" to continue.'
        )
        answer = input(">> ")
        if answer != "yes":
            return

        select_stmt = select(Generation).filter_by(status="completed")
        cursor = self._session.scalars(select_stmt)
        num_exports = 0
        exports_list = list()

        for generation in cursor:
            exports_list.append(json.loads(generation.data))
            generation.status = "exported"
            num_exports += 1

        if not num_exports:
            print("No generations found.")
            return

        with open(self._json_path, "w", encoding="utf-8") as fp:
            json.dump(exports_list, fp)

        self._session.commit()
        print(f"Exported {num_exports} exports.")

    def compress_output(self) -> None:
        print("Starting compression.")

        zip_count = 0
        file_list = os.listdir(self._images_folder)

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

        shutil.rmtree(self._images_folder)
        print("Finished compression.")