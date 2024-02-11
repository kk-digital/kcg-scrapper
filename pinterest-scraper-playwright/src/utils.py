import random
import urllib.parse
from pathlib import Path
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db import Url


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
