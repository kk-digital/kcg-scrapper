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
        self._json_path = path.join(self._images_folder, "images-data.json")
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

    # def compress_output(self) -> None:
    #     print('Starting compression.')
    #     json_db_exists = path.isfile(self._json_path)
    #     if not json_db_exists:
    #         print('Could not found json db.')
    #         return
    #
    #     zip_name = 'compressed-output'
    #     zip_path = path.join(self._output_folder, zip_name)
    #
    #     # first make a single archive
    #     shutil.make_archive(base_name=zip_path, format='zip', root_dir=self._images_folder)
    #
    #     # split into chunks of max size
    #     with open(zip_path + '.zip', 'rb') as fp:
    #         content = fp.read(self._max_archive_size)
    #         file_count = 0
    #         while content:
    #             file_count_str = str(file_count).zfill(6)
    #             zip_file = zipfile.ZipFile(file=f'{zip_path}-{file_count_str}.zip', mode='w')
    #             zip_file.writestr(zinfo_or_arcname=zip_name + '.zip', data=content)
    #             zip_file.close()
    #
    #             content = fp.read(self._max_archive_size)
    #             file_count += 1
    #
    #     shutil.rmtree(self._images_folder)
    #     os.remove(zip_path + '.zip')
    #     print('Finished compression.')
