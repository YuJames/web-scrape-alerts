from logging import (
    DEBUG, INFO, WARNING, ERROR
)
from os import (
    path
)

from .logger import (
    Logger
)

FILE_DIR = path.dirname(path.realpath(__file__))

logger = Logger(
    log_folder=path.join(FILE_DIR, "..", "..", "logs"),
    levels={DEBUG: "debug", INFO: "info", WARNING: "warning", ERROR: "error"}
)

DEBUG, INFO, WARNING, ERROR = DEBUG, INFO, WARNING, ERROR
