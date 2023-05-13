import csv
import itertools
import logging
import os
import time
from functools import wraps
from typing import Callable

from settings import PROXY_LIST_PATH

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


def init_proxy() -> Callable | None:
    if not PROXY_LIST_PATH:
        return

    with open(PROXY_LIST_PATH, "r", newline="", encoding="utf-8") as fh:
        csv_reader = csv.reader(fh)
        proxy_list = [row[0] for row in csv_reader]

    proxy_list = itertools.cycle(proxy_list)

    manifest_json = """
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
    background_js = """
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
    extension_name = "proxies_extension"
    os.makedirs(extension_name, exist_ok=True)

    def build_next_proxy_extension() -> str:
        nonlocal background_js
        proxy = next(proxy_list)
        logger.debug(f"Using proxy: {proxy}")
        endpoint, port, username, password = proxy.split(":")
        new_background_js = background_js % (endpoint, port, username, password)

        files_to_create = {
            "manifest.json": manifest_json,
            "background.js": new_background_js,
        }
        for basename, content in files_to_create.items():
            file_path = f"{extension_name}/{basename}"
            with open(file_path, "w", encoding="utf-8") as fh:
                fh.write(content)

        return extension_name

    return build_next_proxy_extension
