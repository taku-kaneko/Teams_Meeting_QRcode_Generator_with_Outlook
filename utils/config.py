import json
import os
from os.path import expanduser

from utils.logger import get_logger

logger = get_logger(__name__)

CONFIG_PATH = expanduser("~") + "\\Documents\\TeamsQRcoder\\config.json"


def initialize_config():
    if not os.path.isfile(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        config = {
            "update_duration": 60,
            "display_duration": 5,
            "redisplay_duration": 1,
            "isCheckQRcodeInOffice": True,
        }

        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f)
            logger.info("Created initial config.json")
    else:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            logger.info("Load config.json")

    print("|---------- configuration ----------|")
    for key, val in config.items():
        print(f"   {key}: {val}")
    print("|-----------------------------------|")

    return config


def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)
        logger.info("Saved config.json")
