import json
import logging
import os

logger = logging.getLogger(__name__)


def load_json_file(base_path, filename):
    """Load JSON file - called once at startup."""
    path = os.path.join(base_path, filename)

    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Could not find file: %s", path)
        return []
    except json.JSONDecodeError:
        logger.error("Could not decode JSON in: %s", path)
        return []


def find_item_by_id(data_list, search_value, key="id"):
    return next((item for item in data_list if item.get(key) == search_value), None)