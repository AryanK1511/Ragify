# app/utils/logger.py

import logging

import coloredlogs
from config import settings

logger = logging.getLogger(__name__)

field_styles = {
    "levelname": {"color": "cyan", "bold": True},
    "filename": {"color": "magenta"},
    "message": {"color": "white"},
}


log_format = "%(levelname)s | (%(filename)s): %(message)s"

coloredlogs.install(
    level=settings.LOG_LEVEL,
    logger=logger,
    fmt=log_format,
    field_styles=field_styles,
)


class CustomLogger:
    @staticmethod
    def create_log(log_type: str, message: str):
        if log_type == "debug":
            logger.debug(message)
        elif log_type == "warning":
            logger.warning(message)
        elif log_type == "error":
            logger.error(message)
        elif log_type == "critical":
            logger.critical(message)
        else:
            logger.info(message)
