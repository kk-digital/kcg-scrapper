import csv
import itertools
from typing import Iterable

import requests
import tenacity

import settings


class Client:
    def __init__(self) -> None:
        self._proxy_list = iter(self._get_proxy_list())
        self._session = requests.Session()

    @staticmethod
    def _get_proxy_list() -> Iterable:
        with open(settings.PROXY_LIST, "r", newline="") as fp:
            csv_reader = csv.reader(fp)
            proxy_list = [row[0] for row in csv_reader]

        proxy_list = [
            {"http": f"http://{proxy}", "https": f"http://{proxy}"}
            for proxy in proxy_list
        ]

        return itertools.cycle(proxy_list)

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type((requests.HTTPError, requests.Timeout)),
        stop=tenacity.stop_after_attempt(settings.MAX_RETRY),
    )
    def make_request(self, url: str, params: dict = None) -> requests.Response:
        proxy = next(self._proxy_list)
        print(f"Using proxy: {proxy['http']}")
        response = self._session.get(url, params=params, proxies=proxy)
        response.raise_for_status()

        return response

    def close(self) -> None:
        self._session.close()
