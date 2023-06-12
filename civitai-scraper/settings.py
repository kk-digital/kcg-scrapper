# database to use
SQLITE_NAME = "civitai.sqlite"
# time between requests
DOWNLOAD_DELAY = 0
# n of attempts when a request fails
MAX_RETRY = 3
# delay before retry when api crashes
RETRY_DELAY = 30
# name of proxy csv file
PROXY_LIST = None  # location or None
# output path
FILES_STORE = "/output"
# max size for zip files
MAX_ARCHIVE_SIZE = 500 * 1024 * 1024  # 500MB
