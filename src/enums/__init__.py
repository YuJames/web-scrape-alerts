# ~~~~  IMPORTS  ~~~~ #
from .env import (
    AppEnv,
    PrivateEnvKeys,
    PublicEnvKeys
)
from .format import (
    FileFormats
)
from .http import (
    StatusCodes
)
from .logging import (
    LEVEL_MAP,
    LogLevels
)

# ~~~~  PRIVATE GLOBAL VARIABLES  ~~~~ #

# ~~~~  PUBLIC GLOBAL VARIABLES  ~~~~ #
DEV = AppEnv["DEV"]
PROD = AppEnv["PROD"]
APP_ENV_ALL = AppEnv.all()
APP_HOST = PublicEnvKeys["APP_HOST"]
APP_PORT = PublicEnvKeys["APP_PORT"]
ENV = PublicEnvKeys["ENV"]
REDIS_HOST = PublicEnvKeys["REDIS_HOST"]
REDIS_PORT = PublicEnvKeys["REDIS_PORT"]
PUBLIC_ENV_ALL = PublicEnvKeys.all()

CSV = FileFormats["CSV"]
JSON = FileFormats["JSON"]
FILE_FORMATS_ALL = FileFormats.all()

OK = StatusCodes["OK"]
REQUEST_ERROR = StatusCodes["REQUEST_ERROR"]
SERVER_ERROR = StatusCodes["SERVER_ERROR"]
STATUS_CODES_ALL = StatusCodes.all()

DEBUG = LogLevels["DEBUG"]
INFO = LogLevels["INFO"]
WARNING = LogLevels["WARNING"]
ERROR = LogLevels["ERROR"]
CRITICAL = LogLevels["CRITICAL"]
LOG_LEVELS_ALL = LogLevels.all()
LEVEL_MAP = LEVEL_MAP


# ~~~~  PRIVATE CLASSES  ~~~~ #

# ~~~~  PUBLIC CLASSES  ~~~~ #

# ~~~~  PRIVATE FUNCTIONS  ~~~~ #

# ~~~~  PUBLIC FUNCTIONS  ~~~~ #

# ~~~~  DEAD CODE  ~~~~ #
