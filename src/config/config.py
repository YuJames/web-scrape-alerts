# ~~~~  IMPORTS  ~~~~ #
from os import (
    environ
)

from enums import (
    DEV, PROD,
    APP_HOST, APP_PORT, ENV, REDIS_HOST, REDIS_PORT,
    APP_ENV_ALL
)

# ~~~~  PRIVATE GLOBAL VARIABLES  ~~~~ #

# ~~~~  PUBLIC GLOBAL VARIABLES  ~~~~ #

# ~~~~  PRIVATE CLASSES  ~~~~ #

# ~~~~  PUBLIC CLASSES  ~~~~ #
class Config:
    def __init__(self):
        """Application metadata/configurations.

        Args:
            N/A
        """

        # metadata
        self.app_name = "Shopping Web Alert API"
        self.app_description = "A REST API that performs site scraping and alerting."
        self.app_version = "1.0.0"
        self.author_name = "james yu"
        self.author_email = "yujames33@gmail.com"
        self.author_url = ""
        self.repo = ""
        # app configs
        self.host = self.get_env(APP_HOST) if self.get_env(APP_HOST) is not None else "0.0.0.0"
        self.port = self.get_env(APP_PORT) if self.get_env(APP_HOST) is not None else "9000"
        self.env = self.get_env(ENV) if self.get_env(ENV) in APP_ENV_ALL else DEV
        self.timeout = 900

    @staticmethod
    def get_env(key):
        """Get environment variable.

        Args:
            key (str): variable name
        Returns:
            (str): variable value, or None
        """

        env = environ.get(key, "")
        if env.strip() == "":
            env = None

        return env

# ~~~~  PRIVATE FUNCTIONS  ~~~~ #

# ~~~~  PUBLIC FUNCTIONS  ~~~~ #

# ~~~~  DEAD CODE  ~~~~ #
