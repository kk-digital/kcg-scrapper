import os

OUTPUT_FOLDER = os.environ["OUTPUT_FOLDER"]
SQLITE_NAME = "midjourney.sqlite"
LOGGING_LEVEL = os.environ["LOGGING_LEVEL"]
HEADED = True if os.environ["HEADED"] == "true" else False
ACTIONS_DELAY = 100  # ms
SCROLL_DELAY = 4000  # ms
DOWNLOAD_DELAY = 4000  # ms
SCROLL_TIMES = 30
MAX_RETRY = 3
VIEWPORT_SIZES = [(1536, 864), (1440, 900), (1366, 768), (1920, 1080)]
PROXY_LIST = os.getenv("PROXY_LIST", None)  # csv file path