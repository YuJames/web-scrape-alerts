# ~~~~  IMPORTS  ~~~~ #
from enum import (
    EnumMeta
)

# ~~~~  PRIVATE GLOBAL VARIABLES  ~~~~ #

# ~~~~  PUBLIC GLOBAL VARIABLES  ~~~~ #

# ~~~~  PRIVATE CLASSES  ~~~~ #

# ~~~~  PUBLIC CLASSES  ~~~~ #
class EnumBase(EnumMeta):
    """Base class for all enums, to enable improved access to enum values.
    """

    def __getitem__(self, name):
        try:
            return super().__getitem__(name.upper()).value
        except Exception as e:
            return None

    def all(self):
        """Get all values.

        Args:
            N/A
        Returns:
            (list): all enum values
        """

        return [x.value for x in self]

# ~~~~  PRIVATE FUNCTIONS  ~~~~ #

# ~~~~  PUBLIC FUNCTIONS  ~~~~ #

# ~~~~  DEAD CODE  ~~~~ #
