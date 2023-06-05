import csv
import itertools
from typing import Iterable

import settings


def get_proxy_list() -> Iterable:
    with open(settings.PROXY_LIST, "r", newline="") as fp:
        csv_reader = csv.reader(fp)
        proxy_list = [row[0] for row in csv_reader]

    proxy_list = [
        {"http": f"http://{proxy}", "https": f"http://{proxy}"} for proxy in proxy_list
    ]

    return itertools.cycle(proxy_list)
