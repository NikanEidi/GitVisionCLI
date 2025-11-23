import json
import logging
from pathlib import Path
from typing import Dict, Any

# We'll use the __file__ magic to find config.json relative to this file
CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
logger = logging.getLogger(__name__)


def load_config() -> Dict[str, Any]:
    """
    Loads config.json from gitvisioncli/config/
    Returns a Python dictionary.
    Raises FileNotFoundError if missing.
    """

    if not CONFIG_PATH.exists():
        logger.error(f"Config file not found at: {CONFIG_PATH}")
        raise FileNotFoundError(
            f"Config file not found at: {CONFIG_PATH}\n"
            "Please create config.json with your 'api_key' and 'github' token."
        )

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config.json: {e}")
        raise ValueError(
            f"Error parsing config.json: {e}\n"
            "Please ensure config.json is valid JSON."
        )


def save_config(data: Dict[str, Any]) -> None:
    """
    Write configuration back to config.json.
    """
    try:
        with CONFIG_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        logger.error(f"Error saving config.json: {e}")