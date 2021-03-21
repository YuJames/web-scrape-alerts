# ~~~~  IMPORTS  ~~~~ #
from enum import (
    Enum
)

from .base import (
    EnumBase
)

# ~~~~  PRIVATE GLOBAL VARIABLES  ~~~~ #

# ~~~~  PUBLIC GLOBAL VARIABLES  ~~~~ #

# ~~~~  PRIVATE CLASSES  ~~~~ #

# ~~~~  PUBLIC CLASSES  ~~~~ #
class AppEnv(Enum, metaclass=EnumBase):
    """Application run environment.
    """

    DEV = "development"
    PROD = "production"

class PrivateEnvKeys(Enum, metaclass=EnumBase):
    """Application private environment keys.
    """

    pass

class PublicEnvKeys(Enum, metaclass=EnumBase):
    """Application public environment keys.
    """

    APP_HOST = "APPLICATION_HOST"
    APP_PORT = "APPLICATION_PORT"
    ENV = "ENVIRONMENT"
    REDIS_HOST = "REDIS_HOST"
    REDIS_PORT = "REDIS_PORT"

# ~~~~  PRIVATE FUNCTIONS  ~~~~ #

# ~~~~  PUBLIC FUNCTIONS  ~~~~ #

# ~~~~  DEAD CODE  ~~~~ #
