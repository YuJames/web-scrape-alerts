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
class FileFormats(Enum, metaclass=EnumBase):
    """File formats.
    """

    CSV = "csv"
    JSON = "json"

# ~~~~  PRIVATE FUNCTIONS  ~~~~ #

# ~~~~  PUBLIC FUNCTIONS  ~~~~ #

# ~~~~  DEAD CODE  ~~~~ #
