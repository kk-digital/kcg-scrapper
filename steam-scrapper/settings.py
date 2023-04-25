# Scrapy settings for steam_scraping project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import copy
import logging
import os
from os import path
from pathlib import Path

import scrapy.utils.log
from colorlog import ColoredFormatter

# MODIFIABLE

# whether to download videos or gif
DOWNLOAD_VIDEOS = False
# output folder
OUTPUT_FOLDER = r'output'

# set the database to use
JOBS_DB_NAME = "small-apps-db.json"

# DON'T MODIFY

# modify here the name of output file
# now handled with custom json pipeline
# FEEDS = {'data.jsonl': {
#     'format': 'jsonl',
#     'encoding': 'utf8',
#     'store_empty': True,
#     'fields': ['app_id', 'url', 'game_title', 'publisher', 'developer', 'publish_date', 'tags', 'review_count',
#                'positive_review_count', 'negative_review_count', 'images_path', 'videos_path'],
#     'indent': 4,
#     # whether overwrite or append
#     'overwrite': False
# }}


OUTPUT_FOLDER = Path(OUTPUT_FOLDER).expanduser()
FILES_STORE = path.join(OUTPUT_FOLDER, 'apps')
WARC_STORE = path.join(OUTPUT_FOLDER, 'warc-files')
# creating files folder
os.makedirs(WARC_STORE, exist_ok=True)

# set config file location of warcio in env variable
os.environ["SCRAPY_WARCIO_SETTINGS"] = "warcio-settings.yml"

BOT_NAME = "steam_scraping"

SPIDER_MODULES = ["steam_scraping.spiders"]
NEWSPIDER_MODULE = "steam_scraping.spiders"

FAKEUSERAGENT_PROVIDERS = [
    "scrapy_fake_useragent.providers.FakeUserAgentProvider",  # this is the first provider we'll try
    "scrapy_fake_useragent.providers.FakerProvider",
    # if FakeUserAgentProvider fails, we'll use faker to generate a user-agent string for us
    "scrapy_fake_useragent.providers.FixedUserAgentProvider",  # fall back to USER_AGENT value
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 "
    "Safari/537.36"
)

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 2
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# redirect
REDIRECT_ENABLED = False

# depth middleware
# DEPTH_STATS_VERBOSE = True
# high priority for media to be downloaded first
DEPTH_PRIORITY = -100

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
              "application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en,es;q=0.9",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "DNT": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "sec-ch-ua": '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    "steam_scraping.middlewares.SteamScrapingSpiderMiddleware": 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "steam_scraping.middlewares.WarcioDownloaderMiddleware": 80,
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
    "scrapy_fake_useragent.middleware.RandomUserAgentMiddleware": 500,
    "scrapy_fake_useragent.middleware.RetryUserAgentMiddleware": 550,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "steam_scraping.pipelines.MyFilesPipeline": 10,
    "steam_scraping.pipelines.SetDefaultPipeline": 20,
    "steam_scraping.pipelines.SaveItemAsJSONPipeline": 100,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 2
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = True

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# logging config

LOG_ENABLED = True
LOG_LEVEL = "INFO"
DOWNLOAD_WARNSIZE = 0

logging.getLogger("scrapy_warcio.warcio").setLevel("WARNING")

apps_logger = logging.getLogger("apps")
apps_logger.propagate = True
apps_file_handler = logging.FileHandler(path.join(OUTPUT_FOLDER, 'error_logs.log'), "a", "utf-8")
apps_file_handler.setLevel('WARNING')
apps_file_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s"
)
apps_file_handler.setFormatter(apps_file_formatter)
apps_logger.addHandler(apps_file_handler)

# coloring scrapy output
color_formatter = ColoredFormatter(
    (
        "%(log_color)s%(levelname)-5s%(reset)s "
        "%(yellow)s[%(asctime)s]%(reset)s"
        "%(white)s %(name)s %(funcName)s %(bold_purple)s:%(lineno)d%(reset)s "
        "%(log_color)s%(message)s%(reset)s"
    ),
    datefmt="%y-%m-%d %H:%M:%S",
    log_colors={
        "DEBUG": "blue",
        "INFO": "bold_cyan",
        "WARNING": "red",
        "ERROR": "bg_bold_red",
        "CRITICAL": "red,bg_white",
    },
)

_get_handler = copy.copy(scrapy.utils.log._get_handler)


def _get_handler_custom(*args, **kwargs):
    handler = _get_handler(*args, **kwargs)
    handler.setFormatter(color_formatter)
    return handler


scrapy.utils.log._get_handler = _get_handler_custom
