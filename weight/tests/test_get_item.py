from unittest.mock import patch
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../weight-app')))

from main import app


@patch("main.get_item_data")
def test_get_item_truck_success(mock_get_item_data):
    mock_get_item_data.return_value = {
        "id": "TRUCK-1",
        "tara": 12000,
        "sessions": [1, 2],
    }

    client = app.test_client()
    resp = client.get("/item/TRUCK-1")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["id"] == "TRUCK-1"
    assert data["tara"] == 12000
    assert data["sessions"] == [1, 2]
    mock_get_item_data.assert_called_once_with("TRUCK-1", None, None)


@patch("main.get_item_data")
def test_get_item_container_success(mock_get_item_data):
    mock_get_item_data.return_value = {
        "id": "CONT-001",
        "tara": "na",
        "sessions": [3],
    }

    client = app.test_client()
    resp = client.get("/item/CONT-001")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["id"] == "CONT-001"
    assert data["tara"] == "na"
    assert data["sessions"] == [3]
    mock_get_item_data.assert_called_once_with("CONT-001", None, None)


@patch("main.get_item_data")
def test_get_item_not_found(mock_get_item_data):
    mock_get_item_data.return_value = None

    client = app.test_client()
    resp = client.get("/item/NO-SUCH-ID")
    data = resp.get_json()

    assert resp.status_code == 404
    assert data["error"] == "item not found"
    mock_get_item_data.assert_called_once_with("NO-SUCH-ID", None, None)


@patch("main.get_item_data")
def test_get_item_passes_from_and_to_query_params(mock_get_item_data):
    mock_get_item_data.return_value = {
        "id": "TRUCK-9",
        "tara": "na",
        "sessions": [],
    }

    client = app.test_client()
    resp = client.get("/item/TRUCK-9?from=20260301000000&to=20260310123045")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["id"] == "TRUCK-9"
    assert data["tara"] == "na"
    assert data["sessions"] == []

    mock_get_item_data.assert_called_once_with(
        "TRUCK-9",
        "20260301000000",
        "20260310123045",
    )


@patch("main.get_item_data")
def test_get_item_empty_sessions_is_valid(mock_get_item_data):
    mock_get_item_data.return_value = {
        "id": "CONT-404",
        "tara": "na",
        "sessions": [],
    }

    client = app.test_client()
    resp = client.get("/item/CONT-404")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["id"] == "CONT-404"
    assert data["tara"] == "na"
    assert data["sessions"] == []