# ~~~~  IMPORTS  ~~~~ #
from enum import (
    Enum
)
from logging import (
    DEBUG, INFO, WARNING, ERROR, CRITICAL,
    getLevelName
)
from .base import (
    EnumBase
)

# ~~~~  PRIVATE GLOBAL VARIABLES  ~~~~ #

# ~~~~  PUBLIC GLOBAL VARIABLES  ~~~~ #

# ~~~~  PRIVATE CLASSES  ~~~~ #

# ~~~~  PUBLIC CLASSES  ~~~~ #
class LogLevels(Enum, metaclass=EnumBase):
    """Application logging levels.
    """

    DEBUG = getLevelName(DEBUG)
    INFO = getLevelName(INFO)
    WARNING = getLevelName(WARNING)
    ERROR = getLevelName(ERROR)
    CRITICAL = getLevelName(CRITICAL)

LEVEL_MAP = {
    LogLevels["DEBUG"]: DEBUG,
    LogLevels["INFO"]: INFO,
    LogLevels["WARNING"]: WARNING,
    LogLevels["ERROR"]: ERROR,
    LogLevels["CRITICAL"]: CRITICAL
}

# ~~~~  PRIVATE FUNCTIONS  ~~~~ #

# ~~~~  PUBLIC FUNCTIONS  ~~~~ #

# ~~~~  DEAD CODE  ~~~~ #
