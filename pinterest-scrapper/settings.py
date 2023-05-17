# logging level, e.g. if set to warning no debug and info logs are sent to console nor log files
LOG_LEVEL = "DEBUG"

# path to output folder, relative and absolute allowed
# can also set it with --output flag on cli
OUTPUT_FOlDER = "output"
# proxy list csv file path
PROXY_LIST_PATH = None
# time before rotate proxy in mins
PROXY_ROTATE_MINUTES = 15

# name of sqlite db the app will create to store persistent state of jobs
DATABASE_NAME = "pinterest.sqlite"

# delay between scrolls when scraping boards and pins
SCROLL_DELAY = 0.5
# delay between requests to pin page and pin img
DOWNLOAD_DELAY = 2

# max time an operation such as page loading or finding an element on dom
# waits before raising an exception
TIMEOUT = 30

# number of retries in case of exception such as Timeout and NoSuchElement
MAX_RETRY = 5
# max size before compressing
MAX_OUTPUT_SIZE_MB = 500  # MB

# DO NOT MODIFY
# max size in bytes
MAX_OUTPUT_SIZE = MAX_OUTPUT_SIZE_MB * (1024 * 1024)  # bytes
