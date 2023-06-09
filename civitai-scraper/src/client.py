import csv
import random
from typing import Optional

import requests
import tenacity

import settings


class Client:
    def __init__(self) -> None:
        self._proxy_list = self._get_proxy_list()
        self._session = requests.Session()

    def _get_proxy_list(self) -> Optional[list]:
        if not settings.PROXY_LIST:
            print("Not using proxies.")
            return

        with open(settings.PROXY_LIST, "r", newline="") as fp:
            csv_reader = csv.reader(fp)
            proxy_list = [row[0] for row in csv_reader]

        proxy_list = [
            {"http": f"http://{proxy}", "https": f"http://{proxy}"}
            for proxy in proxy_list
        ]

        return proxy_list

    def _get_random_proxy(self) -> dict:
        return random.choice(self._proxy_list)

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type((requests.HTTPError, requests.Timeout)),
        stop=tenacity.stop_after_attempt(settings.MAX_RETRY),
        reraise=True,
    )
    def make_request(self, url: str, params: dict = None) -> requests.Response:
        proxy = None
        if settings.PROXY_LIST:
            proxy = self._get_random_proxy()
            print(f"Using proxy: {proxy['http']}.")

        print(f"Getting url: {url}.")
        response = self._session.get(url, params=params, proxies=proxy)
        response.raise_for_status()

        return response

    def close(self) -> None:
        self._session.close()
