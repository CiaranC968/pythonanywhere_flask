import json
import os


def load_json_file(app_root, filename):
    """Load JSON file - called once at startup."""
    path = os.path.join(app_root, "data", filename)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def find_item_by_id(data, value, id_field="id"):
    return next((item for item in data if item.get(id_field) == value), None)