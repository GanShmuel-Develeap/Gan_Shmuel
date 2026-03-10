import os
import requests


def _weight_get(path, params=None):
    base = os.getenv("WEIGHT_API_URL")
    response = requests.get(f"{base}{path}", params=params)

    if response.status_code == 404:
        return None, "Not found"

    response.raise_for_status()
    return response.json(), None


def get_item(item_id, params=None):
    return _weight_get(f"/item/{item_id}", params)


def get_weights(params=None):
    return _weight_get("/weight", params)