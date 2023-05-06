import csv
import itertools
import logging
import threading
import time
from functools import wraps
from typing import Callable

logger = logging.getLogger(f"scraper.{__name__}")


def time_perf(log_str: str):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = f(*args, **kwargs)
            end = time.perf_counter()
            elapsed_min = (end - start) / 60
            logger.info(f"Took {elapsed_min:.2f} minutes to {log_str}.")

            return result

        return wrapper

    return decorator


def init_proxy_list(proxy_list_path: str) -> Callable:
    lock = threading.Lock()

    with open(proxy_list_path, "r", newline="", encoding="utf-8") as fh:
        csv_reader = csv.reader(fh)
        proxy_list = [row[0] for row in csv_reader]

    proxy_list = itertools.cycle(proxy_list)

    def get_next_proxy() -> str:
        with lock:
            return next(proxy_list)

    return get_next_proxy
