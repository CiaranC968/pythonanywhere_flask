import json
import os


def load_json_file(base_path, filename):
    """Load JSON file - called once at startup."""
    path = os.path.join(base_path, filename)

    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Warning: Could not find file: {path}")
        return []
    except json.JSONDecodeError:
        print(f"⚠️ Error: Could not decode JSON in: {path}")
        return []


def find_item_by_id(data_list, search_value, key="id"):
    return next((item for item in data_list if item.get(key) == search_value), None)