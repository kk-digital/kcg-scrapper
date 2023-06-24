import logging.handlers
import os
from os import path

from colorlog import ColoredFormatter

import settings


def configure() -> None:
    # formats
    log_format = "%(asctime)s - %(threadName)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s"
    date_format = "%m-%d %H:%M:%S"
    # folder creation
    log_path = path.join(settings.OUTPUT_FOLDER, "logs")
    os.makedirs(log_path, exist_ok=True)

    logger = logging.getLogger("scraper")
    logger.setLevel(settings.LOGGING_LEVEL)
    # console handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_formatter = ColoredFormatter("%(log_color)s" + log_format, date_format)
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)
    # rotating file handler
    filename = path.join(log_path, "logs.log")
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=filename, when="midnight", interval=1, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
