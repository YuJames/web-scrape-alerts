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
class StatusCodes(Enum, metaclass=EnumBase):
    """File formats.
    """

    OK = 200
    REQUEST_ERROR = 400
    SERVER_ERROR = 500

# ~~~~  PRIVATE FUNCTIONS  ~~~~ #

# ~~~~  PUBLIC FUNCTIONS  ~~~~ #

# ~~~~  DEAD CODE  ~~~~ #
