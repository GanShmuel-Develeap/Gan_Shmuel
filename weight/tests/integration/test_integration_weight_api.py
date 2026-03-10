from pathlib import Path
import sys
import json

# allow importing the app
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "weight-app"))

from main import app
from db import get_conn


def test_weight_api_post_in_transaction():
    """Test POST /weight endpoint for IN direction transaction."""
    client = app.test_client()

    payload = {
        "direction": "in",
        "truck": "TEST-TRUCK-001",
        "containers": "TEST-C-1,TEST-C-2",
        "weight": 5000,
        "unit": "kg",
        "produce": "test_produce"
    }

    response = client.post("/weight", json=payload)
    data = response.get_json()

    assert response.status_code == 201
    assert data["status"] == "success"
    assert "id" in data
    assert data["truck"] == "TEST-TRUCK-001"
    assert data["bruto"] == 5000
    
    # Verify transaction was inserted into database
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM transactions WHERE id = %s", (int(data["id"]),))
    tx = cur.fetchone()
    cur.close()
    conn.close()
    
    assert tx is not None
    assert tx["direction"] == "in"
    assert tx["truck"] == "TEST-TRUCK-001"
    assert tx["bruto"] == 5000
    
    # Cleanup
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions WHERE id = %s", (int(data["id"]),))
    conn.commit()
    cur.close()
    conn.close()


def test_weight_api_post_out_transaction():
    """Test POST /weight endpoint for OUT direction transaction."""
    client = app.test_client()

    # First insert an IN transaction
    in_payload = {
        "direction": "in",
        "truck": "TEST-TRUCK-002",
        "containers": "TEST-C-3",
        "weight": 5500,
        "unit": "kg",
        "produce": "test_produce_2"
    }

    in_response = client.post("/weight", json=in_payload)
    in_data = in_response.get_json()
    assert in_response.status_code == 201

    # Now insert an OUT transaction
    out_payload = {
        "direction": "out",
        "truck": "TEST-TRUCK-002",
        "weight": 5200,
        "unit": "kg"
    }

    out_response = client.post("/weight", json=out_payload)
    out_data = out_response.get_json()

    assert out_response.status_code == 201
    assert out_data["status"] == "success"
    assert "id" in out_data
    assert out_data["truck"] == "TEST-TRUCK-002"
    assert out_data["truckTara"] == 5200
    
    # Cleanup
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions WHERE truck = %s", ("TEST-TRUCK-002",))
    conn.commit()
    cur.close()
    conn.close()


def test_weight_api_post_none_direction():
    """Test POST /weight endpoint for NONE direction (standalone container)."""
    client = app.test_client()

    payload = {
        "direction": "none",
        "containers": "TEST-C-4",
        "weight": 100,
        "unit": "kg",
        "produce": "test_container"
    }

    response = client.post("/weight", json=payload)
    data = response.get_json()

    assert response.status_code == 201
    assert data["status"] == "success"
    assert data["truck"] == "na"
    assert data["bruto"] == 100
    
    # Cleanup
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions WHERE id = %s", (int(data["id"]),))
    conn.commit()
    cur.close()
    conn.close()


def test_weight_api_truck_defaults_to_na():
    """Test that truck defaults to 'na' when not provided in API."""
    client = app.test_client()

    payload = {
        "direction": "none",
        "containers": "TEST-C-5",
        "weight": 200,
        "unit": "kg"
    }

    response = client.post("/weight", json=payload)
    data = response.get_json()

    assert response.status_code == 201
    assert data["truck"] == "na"
    
    # Cleanup
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions WHERE id = %s", (int(data["id"]),))
    conn.commit()
    cur.close()
    conn.close()


def test_weight_api_out_without_in_fails():
    """Test that OUT without prior IN fails."""
    client = app.test_client()

    payload = {
        "direction": "out",
        "truck": "NONEXISTENT-TRUCK",
        "weight": 5000,
        "unit": "kg"
    }

    response = client.post("/weight", json=payload)
    data = response.get_json()

    assert response.status_code == 400
    assert data["status"] == "error"
    assert "prior IN" in data["message"] or "No prior" in data["message"]


def test_weight_api_missing_required_fields():
    """Test that API returns error for missing required fields."""
    client = app.test_client()

    # Missing direction
    response = client.post("/weight", json={"weight": 5000})
    assert response.status_code == 400
    assert response.get_json()["status"] == "error"

    # Missing weight
    response = client.post("/weight", json={"direction": "in", "containers": "C-1"})
    assert response.status_code == 400
    assert response.get_json()["status"] == "error"


def test_weight_api_invalid_weight_type():
    """Test that API returns error for non-numeric weight."""
    client = app.test_client()

    payload = {
        "direction": "in",
        "containers": "TEST-C-6",
        "weight": "not_a_number",
        "unit": "kg"
    }

    response = client.post("/weight", json=payload)
    data = response.get_json()

    assert response.status_code == 400
    assert data["status"] == "error"
    assert "number" in data["message"].lower()


def test_weight_api_default_unit_kg():
    """Test that unit defaults to 'kg' when not provided."""
    client = app.test_client()

    payload = {
        "direction": "none",
        "containers": "TEST-C-7",
        "weight": 150
    }

    response = client.post("/weight", json=payload)
    data = response.get_json()

    assert response.status_code == 201
    
    # Verify in database that unit is 'kg'
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT unit FROM transactions WHERE id = %s", (int(data["id"]),))
    tx = cur.fetchone()
    cur.close()
    conn.close()
    
    assert tx["unit"] == "kg"
    
    # Cleanup
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions WHERE id = %s", (int(data["id"]),))
    conn.commit()
    cur.close()
    conn.close()


def test_weight_api_form_data_submission():
    """Test POST /weight endpoint with form data instead of JSON."""
    client = app.test_client()

    form_data = {
        "direction": "in",
        "truck": "TEST-TRUCK-003",
        "containers": "TEST-C-8",
        "weight": "3500",
        "unit": "kg",
        "produce": "test_produce_3"
    }

    response = client.post("/weight", data=form_data)
    data = response.get_json()

    assert response.status_code == 201
    assert data["status"] == "success"
    assert data["bruto"] == 3500
    
    # Cleanup
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions WHERE truck = %s", ("TEST-TRUCK-003",))
    conn.commit()
    cur.close()
    conn.close()
