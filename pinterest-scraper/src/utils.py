import csv
import itertools
import logging
import os
import time
from datetime import datetime
from functools import wraps
from typing import Optional

import settings

logger = logging.getLogger(f"scraper.{__name__}")


def read_csv(filename) -> list:
    with open(filename, "r", newline="", encoding="utf-8") as fh:
        csv_reader = csv.reader(fh)
        return [row for row in csv_reader]


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


_manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Proxies",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """
_background_js = """
    var config = {
            mode: "fixed_servers",
            rules: {
              singleProxy: {
                scheme: "http",
                host: "%s",
                port: parseInt(%s)
              },
              bypassList: ["localhost"]
            }
          };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """
_extension_name = "proxies_extension"
_proxy_list = None
_proxy_list_cycle = None


def get_next_proxy() -> Optional[str]:
    global _proxy_list
    global _proxy_list_cycle

    if not settings.PROXY_LIST_PATH:
        return

    if not _proxy_list:
        with open(settings.PROXY_LIST_PATH, "r", newline="", encoding="utf-8") as fh:
            csv_reader = csv.DictReader(fh)
            _proxy_list = sorted(list(csv_reader), key=lambda x: float(x["lastused"]))

        _proxy_list_cycle = itertools.cycle(_proxy_list)
        os.makedirs(_extension_name, exist_ok=True)

    proxy = next(_proxy_list_cycle)
    proxy["lastused"] = datetime.now().timestamp()
    logger.debug(f"Using proxy: {proxy['proxy']}")
    endpoint, port, username, password = proxy["proxy"].split(":")
    new_background_js = _background_js % (endpoint, port, username, password)

    # write proxy extension
    files_to_create = {
        "manifest.json": _manifest_json,
        "background.js": new_background_js,
    }
    for filename, content in files_to_create.items():
        file_path = f"{_extension_name}/{filename}"
        with open(file_path, "w", encoding="utf-8") as fh:
            fh.write(content)

    # write proxies to persist lastused col
    with open(settings.PROXY_LIST_PATH, "w", encoding="utf-8") as fh:
        csv_writer = csv.DictWriter(fh, fieldnames=["proxy", "lastused"])
        csv_writer.writeheader()
        csv_writer.writerows(_proxy_list)

    return _extension_name
