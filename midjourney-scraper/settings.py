import logging
import os

is_production = True if os.getenv("PYTHON_ENV") == "production" else False

OUTPUT_FOLDER = os.environ["OUTPUT_FOLDER"]
SQLITE_NAME = "midjourney.sqlite"
LOGGING_LEVEL = logging.INFO if is_production else logging.DEBUG
HEADED = not is_production
ACTIONS_DELAY = 100  # ms
SCROLL_DELAY = 4000  # ms
DOWNLOAD_DELAY = 4000  # ms
SCROLL_TIMES = 30
MAX_RETRY = 3
USER_AGENT_LIST = "user-agent-list.json"  # json file path
VIEWPORT_SIZES = [(1536, 864), (1440, 900), (1366, 768), (1920, 1080)]
PROXY_LIST = os.getenv("PROXY_LIST", None)  # csv file path
