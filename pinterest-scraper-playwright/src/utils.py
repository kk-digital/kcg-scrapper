import logging
import random
import urllib.parse
from functools import wraps
from pathlib import Path
from typing import Callable, Iterable

from playwright._impl._errors import TargetClosedError
from playwright.sync_api import TimeoutError
from sqlalchemy import select
from sqlalchemy.orm import Session
from tenacity import after_log, retry, retry_if_exception_type, stop_after_attempt

from src import settings
from src.db import Url

logger = logging.getLogger(__name__)


def insert_urls(urls: Iterable, session: Session) -> None:
    for url in urls:
        session.add(Url(url=url))

    session.commit()


def exclude_duplicates(urls: Iterable, session: Session) -> list[str]:
    new_urls = []
    for url in urls:
        stmt = select(Url).where(Url.url == url)
        result = session.scalars(stmt).first()
        if result is None:
            new_urls.append(url)

    return new_urls


def join_urls(base_url: str, urls: Iterable) -> list[str]:
    return [urllib.parse.urljoin(base_url, url) for url in urls]


def load_proxy_list(proxy_list_path: Path) -> list[dict]:
    proxy_list = []
    with proxy_list_path.open("r", encoding="utf-8") as fp:
        for line in fp:
            [credentials, server] = line.split("@")
            [username, password] = credentials.split(":")
            proxy_list.append(
                {"server": server, "username": username, "password": password}
            )
    random.shuffle(proxy_list)

    return proxy_list


def default_retry(func: Callable) -> Callable:
    @wraps(func)
    @retry(
        retry=retry_if_exception_type((TimeoutError, TargetClosedError)),
        stop=stop_after_attempt(settings.RETRY_TIMES),
        after=after_log(logger, logging.WARNING),
    )
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
