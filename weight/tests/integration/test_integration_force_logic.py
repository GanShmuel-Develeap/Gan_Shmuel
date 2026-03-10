from pathlib import Path
import sys
import json

# allow importing the app
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "weight-app"))

from main import app
from db import get_conn


def cleanup_truck(truck_id):
    """Helper to cleanup transactions for a truck."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions WHERE truck = %s", (truck_id,))
    conn.commit()
    cur.close()
    conn.close()


def test_force_false_duplicate_in_fails():
    """Test that force=false fails when submitting duplicate IN for same truck."""
    client = app.test_client()
    truck_id = "FORCE-TEST-TRUCK-01"
    cleanup_truck(truck_id)

    # First IN transaction
    payload1 = {
        "direction": "in",
        "truck": truck_id,
        "containers": "FORCE-C-1",
        "weight": 5000,
        "unit": "kg",
        "force": False
    }

    response1 = client.post("/weight", json=payload1)
    assert response1.status_code == 201

    # Second IN transaction without OUT (should fail with force=false)
    payload2 = {
        "direction": "in",
        "truck": truck_id,
        "containers": "FORCE-C-2",
        "weight": 5500,
        "unit": "kg",
        "force": False
    }

    response2 = client.post("/weight", json=payload2)
    data2 = response2.get_json()

    assert response2.status_code == 400
    assert data2["status"] == "error"
    assert "open session" in data2["message"].lower() or "force" in data2["message"].lower()

    cleanup_truck(truck_id)


def test_force_true_overwrites_duplicate_in():
    """Test that force=true overwrites existing IN transaction for same truck."""
    client = app.test_client()
    truck_id = "FORCE-TEST-TRUCK-02"
    cleanup_truck(truck_id)

    # First IN transaction
    payload1 = {
        "direction": "in",
        "truck": truck_id,
        "containers": "FORCE-C-3",
        "weight": 5000,
        "unit": "kg",
        "force": False
    }

    response1 = client.post("/weight", json=payload1)
    data1 = response1.get_json()
    tx_id_1 = int(data1["id"])
    assert response1.status_code == 201

    # Second IN transaction with force=true (should overwrite)
    payload2 = {
        "direction": "in",
        "truck": truck_id,
        "containers": "FORCE-C-4",
        "weight": 5500,
        "unit": "kg",
        "force": True
    }

    response2 = client.post("/weight", json=payload2)
    data2 = response2.get_json()
    tx_id_2 = int(data2["id"])

    assert response2.status_code == 201
    assert data2["status"] == "success"
    assert data2["bruto"] == 5500

    # Verify first transaction is deleted
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM transactions WHERE id = %s", (tx_id_1,))
    old_tx = cur.fetchone()
    assert old_tx is None
    cur.close()
    conn.close()

    cleanup_truck(truck_id)


def test_force_false_duplicate_out_fails():
    """Test that force=false fails when submitting duplicate OUT for same session."""
    client = app.test_client()
    truck_id = "FORCE-TEST-TRUCK-03"
    cleanup_truck(truck_id)

    # First IN transaction
    payload_in = {
        "direction": "in",
        "truck": truck_id,
        "containers": "FORCE-C-5",
        "weight": 6000,
        "unit": "kg",
        "force": False
    }

    response_in = client.post("/weight", json=payload_in)
    assert response_in.status_code == 201

    # First OUT transaction
    payload_out1 = {
        "direction": "out",
        "truck": truck_id,
        "weight": 5800,
        "unit": "kg",
        "force": False
    }

    response_out1 = client.post("/weight", json=payload_out1)
    assert response_out1.status_code == 201

    # Second OUT transaction without force (should fail)
    payload_out2 = {
        "direction": "out",
        "truck": truck_id,
        "weight": 5900,
        "unit": "kg",
        "force": False
    }

    response_out2 = client.post("/weight", json=payload_out2)
    data_out2 = response_out2.get_json()

    assert response_out2.status_code == 400
    assert data_out2["status"] == "error"
    assert "OUT" in data_out2["message"] or "force" in data_out2["message"].lower()

    cleanup_truck(truck_id)


def test_force_true_overwrites_duplicate_out():
    """Test that force=true overwrites existing OUT transaction for same session."""
    client = app.test_client()
    truck_id = "FORCE-TEST-TRUCK-04"
    cleanup_truck(truck_id)

    # First IN transaction
    payload_in = {
        "direction": "in",
        "truck": truck_id,
        "containers": "FORCE-C-6",
        "weight": 6500,
        "unit": "kg",
        "force": False
    }

    response_in = client.post("/weight", json=payload_in)
    assert response_in.status_code == 201

    # First OUT transaction
    payload_out1 = {
        "direction": "out",
        "truck": truck_id,
        "weight": 6200,
        "unit": "kg",
        "force": False
    }

    response_out1 = client.post("/weight", json=payload_out1)
    data_out1 = response_out1.get_json()
    out_id_1 = int(data_out1["id"])
    assert response_out1.status_code == 201

    # Second OUT transaction with force=true
    payload_out2 = {
        "direction": "out",
        "truck": truck_id,
        "weight": 6300,
        "unit": "kg",
        "force": True
    }

    response_out2 = client.post("/weight", json=payload_out2)
    data_out2 = response_out2.get_json()
    out_id_2 = int(data_out2["id"])

    assert response_out2.status_code == 201
    assert data_out2["status"] == "success"

    # Verify first OUT transaction is deleted
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM transactions WHERE id = %s", (out_id_1,))
    old_out = cur.fetchone()
    assert old_out is None
    cur.close()
    conn.close()

    cleanup_truck(truck_id)


def test_force_not_applied_for_na_truck_in_direction():
    """Test that force logic is skipped for 'na' truck on IN direction."""
    client = app.test_client()

    # First IN with na truck
    payload1 = {
        "direction": "in",
        "truck": "na",
        "containers": "FORCE-C-7",
        "weight": 4000,
        "unit": "kg",
        "force": False
    }

    response1 = client.post("/weight", json=payload1)
    assert response1.status_code == 201

    # Second IN with na truck - should succeed since force logic doesn't apply to 'na'
    payload2 = {
        "direction": "in",
        "truck": "na",
        "containers": "FORCE-C-8",
        "weight": 4500,
        "unit": "kg",
        "force": False
    }

    response2 = client.post("/weight", json=payload2)
    assert response2.status_code == 201  # Should succeed

    # Cleanup both transactions
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions WHERE truck = %s AND direction = 'in'", ("na",))
    conn.commit()
    cur.close()
    conn.close()


def test_force_true_string_value():
    """Test that force='true' (string) is converted to boolean True."""
    client = app.test_client()
    truck_id = "FORCE-TEST-TRUCK-05"
    cleanup_truck(truck_id)

    # First IN transaction
    payload1 = {
        "direction": "in",
        "truck": truck_id,
        "containers": "FORCE-C-9",
        "weight": 5000,
        "unit": "kg",
        "force": False
    }

    response1 = client.post("/weight", json=payload1)
    assert response1.status_code == 201

    # Second IN with force='true' (as string from HTML form)
    payload2 = {
        "direction": "in",
        "truck": truck_id,
        "containers": "FORCE-C-10",
        "weight": 5500,
        "unit": "kg",
        "force": "true"
    }

    response2 = client.post("/weight", json=payload2)
    data2 = response2.get_json()

    assert response2.status_code == 201
    assert data2["status"] == "success"

    cleanup_truck(truck_id)


def test_force_false_string_value():
    """Test that force='false' (string) is converted to boolean False."""
    client = app.test_client()
    truck_id = "FORCE-TEST-TRUCK-06"
    cleanup_truck(truck_id)

    # First IN transaction
    payload1 = {
        "direction": "in",
        "truck": truck_id,
        "containers": "FORCE-C-11",
        "weight": 5000,
        "unit": "kg",
        "force": False
    }

    response1 = client.post("/weight", json=payload1)
    assert response1.status_code == 201

    # Second IN with force='false' (string)
    payload2 = {
        "direction": "in",
        "truck": truck_id,
        "containers": "FORCE-C-12",
        "weight": 5500,
        "unit": "kg",
        "force": "false"
    }

    response2 = client.post("/weight", json=payload2)
    data2 = response2.get_json()

    assert response2.status_code == 400
    assert data2["status"] == "error"

    cleanup_truck(truck_id)
