from unittest.mock import patch, MagicMock
import sys
import os

sys.path.append(os.path.abspath("weight-app"))

from main import app

@patch("main.get_conn")
def test_get_all_transactions(mock_get_conn):

    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_get_conn.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur

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

    mock_cur.fetchall.side_effect = [transactions, containers]

    client = app.test_client()
    resp = client.get("/weight")

    data = resp.get_json()

    assert resp.status_code == 200
    assert data[0]["id"] == 1
    assert data[0]["containers"] == ["CONT-1", "CONT-2"]