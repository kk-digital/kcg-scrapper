import logging
import os

is_production = True if os.getenv("PYTHON_ENV") == "production" else False

OUTPUT_FOLDER = os.environ["OUTPUT_FOLDER"]
LOGGING_LEVEL = logging.INFO if is_production else logging.DEBUG
HEADED = not is_production
ACTIONS_DELAY = 100  # milliseconds
