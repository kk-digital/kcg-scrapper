import csv

from scraper import settings


def load_proxies() -> list[dict]:
    with settings.PROXY_LIST_PATH.open("r", newline="", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        return list(reader)
