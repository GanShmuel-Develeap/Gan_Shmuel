from unittest.mock import patch, MagicMock
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../weight-app')))

from main import app


def make_mock_db(mock_get_conn, transactions, containers):
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_get_conn.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchall.side_effect = [transactions, containers]


@patch("main.get_conn")
def test_get_all_transactions(mock_get_conn):
    transactions = [
        {
            "id": 1,
            "direction": "in",
            "bruto": 1000,
            "neto": 800,
            "unit": "kg",
            "produce": "Apples",
            "containers": "CONT-1,CONT-2",
        }
    ]

    containers = [
        {"container_id": "CONT-1", "weight": 100},
        {"container_id": "CONT-2", "weight": 200},
    ]

    make_mock_db(mock_get_conn, transactions, containers)

    client = app.test_client()
    resp = client.get("/weight")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data[0]["id"] == 1
    assert data[0]["direction"] == "in"
    assert data[0]["produce"] == "Apples"
    assert data[0]["containers"] == ["CONT-1", "CONT-2"]
    assert data[0]["neto"] == 800


@patch("main.get_conn")
def test_get_all_transactions_unknown_container_weight_returns_na(mock_get_conn):
    transactions = [
        {
            "id": 2,
            "direction": "out",
            "bruto": 2000,
            "neto": 1500,
            "unit": "kg",
            "produce": "Bananas",
            "containers": "CONT-1,CONT-2",
        }
    ]

    containers = [
        {"container_id": "CONT-1", "weight": 100},
        {"container_id": "CONT-2", "weight": None},
    ]

    make_mock_db(mock_get_conn, transactions, containers)

    client = app.test_client()
    resp = client.get("/weight")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data[0]["neto"] == "na"


@patch("main.get_conn")
def test_get_all_transactions_lbs_converts_neto_to_kg(mock_get_conn):
    transactions = [
        {
            "id": 3,
            "direction": "in",
            "bruto": 3000,
            "neto": 100,
            "unit": "lbs",
            "produce": "Oranges",
            "containers": None,
        }
    ]

    containers = []

    make_mock_db(mock_get_conn, transactions, containers)

    client = app.test_client()
    resp = client.get("/weight")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data[0]["neto"] == round(100 * 0.45359237)
    assert data[0]["containers"] == []


@patch("main.get_conn")
def test_get_all_transactions_no_containers_returns_empty_list(mock_get_conn):
    transactions = [
        {
            "id": 4,
            "direction": "in",
            "bruto": 1200,
            "neto": 900,
            "unit": "kg",
            "produce": "Pears",
            "containers": None,
        }
    ]

    containers = []

    make_mock_db(mock_get_conn, transactions, containers)

    client = app.test_client()
    resp = client.get("/weight")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data[0]["containers"] == []
    assert data[0]["neto"] == 900


@patch("main.get_conn")
def test_get_all_transactions_filter_query_param(mock_get_conn):
    transactions = [
        {
            "id": 5,
            "direction": "out",
            "bruto": 5000,
            "neto": 4000,
            "unit": "kg",
            "produce": "Mangoes",
            "containers": "CONT-9",
        }
    ]

    containers = [
        {"container_id": "CONT-9", "weight": 250},
    ]

    make_mock_db(mock_get_conn, transactions, containers)

    client = app.test_client()
    resp = client.get("/weight?filter=out")
    data = resp.get_json()

    assert resp.status_code == 200
    assert len(data) == 1
    assert data[0]["direction"] == "out"

    