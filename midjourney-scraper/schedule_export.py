import os
import shutil
from pathlib import Path
from datetime import date
import time

import schedule
from fire import Fire
from sqlalchemy.orm import Session
from sqlalchemy import select, func

if os.getenv("PYTHON_ENV", "development") == "development":
    from dotenv import load_dotenv

    load_dotenv()

import settings
from src.utils import Utils
from src.db import engine as db_engine
from src.db.model import Generation

utils = Utils()
engine = db_engine.get_engine()


def job(filters_path: str):
    weekly_folder = Path(settings.OUTPUT_FOLDER, f"output-{date.today().isoformat()}")
    weekly_folder.mkdir()

    prompt_filters = utils.read_filters(filters_path)
    for prompt_filter in prompt_filters:
        with Session(engine) as session:
            select_stmt = select(func.count(Generation.id)).filter_by(
                prompt_filter=prompt_filter, status="completed"
            )
            count = session.execute(select_stmt).scalar()
            if not count:
                continue

        utils.export_json_data(prompt_filter=prompt_filter, test_export=False)
        utils.compress_output(test_export=False)

        filter_weekly_folder = Path(
            settings.OUTPUT_FOLDER, f"{prompt_filter}-{date.today().isoformat()}"
        )
        filter_weekly_folder.mkdir()

        shutil.move(settings.EXPORT_JSON_PATH, filter_weekly_folder)
        zip_list = Path(settings.OUTPUT_FOLDER).glob("*.zip")
        for zipfile in zip_list:
            shutil.move(zipfile, filter_weekly_folder)

        shutil.make_archive(
            base_name=str(filter_weekly_folder),
            format="zip",
            root_dir=filter_weekly_folder,
        )
        shutil.move(filter_weekly_folder.with_suffix(".zip"), weekly_folder)
        shutil.rmtree(filter_weekly_folder)


def main(filter_path: str, run_now: bool = False):
    if run_now:
        job(filter_path)

    schedule.every().friday.do(job, filter_path)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    Fire(main)
