from datetime import (
    datetime
)
from logging import (
    FileHandler,
    Formatter,
    getLogger
)
from os import (
    path
)

class Logger:
    def __init__(self, log_folder, levels):
        """Smart logic for logging.
        
        Args:
            log_folder (str): path to log folder
            levels (dict): log levels to name
        """
        
        self.loggers = {}
        
        formatter = Formatter("%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s")
        file_template = "{}_{}"
        
        for i, j in levels.items():
            logger = getLogger(j)
            file = file_template.format(
                path.join(log_folder, datetime.now().strftime('log_%Y_%m_%d')),
                j.lower()
            )
            handler = FileHandler(file)
            
            handler.setFormatter(formatter)
            logger.setLevel(i)
            logger.addHandler(handler)
            
            self.loggers[i] = logger
        
    def write(self, level, msg):
        """Write to a log file.
        
        Args:
            level (str): log level
            msg (str): log message
        """
        
        self.loggers[level].log(
            level=level,
            msg=msg
        )
