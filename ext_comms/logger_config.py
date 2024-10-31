# logger_config.py (Additional File Handler)
import logging
from logging.handlers import RotatingFileHandler
from colorlog import ColoredFormatter
from colorlog.escape_codes import escape_codes

# Define a custom level for our specific message
COOLDOWN_END_LEVEL_NUM = 25  # Between INFO (20) and WARNING (30)
logging.addLevelName(COOLDOWN_END_LEVEL_NUM, "COOLDOWN_END")

# Add magenta to escape codes if not present
escape_codes.update({
    'magenta': '\033[35m',
    'reset': '\033[0m'  # reset color after each log line
})

# Custom log method for cooldown_end
def cooldown_end(self, message, *args, **kws):
    if self.isEnabledFor(COOLDOWN_END_LEVEL_NUM):
        self._log(COOLDOWN_END_LEVEL_NUM, message, args, **kws)

# Attach the method to logging.Logger
logging.Logger.cooldown_end = cooldown_end

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        # Console handler with color
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Assign colors to log levels, including our custom level
        formatter = ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s%(reset)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
                'COOLDOWN_END': 'magenta'  # Assign magenta color for the custom level
            }
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler without color
        file_handler = RotatingFileHandler('app.log', maxBytes=5 * 1024 * 1024, backupCount=5)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger