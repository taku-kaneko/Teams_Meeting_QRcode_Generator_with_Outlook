import os
from logging import DEBUG, INFO, WARNING, FileHandler, Formatter, getLogger
from os.path import expanduser

LOG_PATH = filename = expanduser("~") + "\\Documents\\TeamsQRcoder\\log.txt"


def get_logger(logger_name: str = "__main__"):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    fmt = "%(asctime)s %(levelname)s %(name)s :%(message)s"
    logger = getLogger(logger_name)
    logger.setLevel(DEBUG)

    file_handler = FileHandler(LOG_PATH, mode="a", encoding="utf-8")
    file_handler.setLevel(INFO)
    file_handler.setFormatter(Formatter(fmt))

    logger.addHandler(file_handler)

    return logger
