from scraper import settings


def load_proxies() -> list[dict]:
    proxy_list = []
    with settings.PROXY_LIST_PATH.open("r", encoding="utf-8") as fp:
        for line in fp:
            [credentials, server] = line.split("@")
            [username, password] = credentials.split(":")
            proxy_list.append(
                {"server": server, "username": username, "password": password}
            )

    return proxy_list
