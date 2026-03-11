from unittest.mock import patch, MagicMock
from app import app
# ------------------------
# Health Route
# ------------------------
def test_health_ok(client):
    """Health route should return 200 if service is alive."""
    with patch("routes.health_check", return_value=True):
        rv = client.get("/health")
        assert rv.status_code == 200
        assert rv.json == {"message": "Ok"}

def test_health_failure(client):
    """Health route should return 500 if service is down."""
    with patch("routes.health_check", return_value=False):
        rv = client.get("/health")
        assert rv.status_code == 500
        assert rv.json == {"message": "Failure"}

# ------------------------
# Provider Routes
# ------------------------
def test_create_provider_success(client):
    """POST /provider should return 201 with new provider id."""
    with patch("routes.create_provider", return_value=(1, None)):
        rv = client.post("/provider", json={"name": "Test"})
        assert rv.status_code == 201
        assert rv.json == {"id": "1"}

def test_create_provider_conflict(client):
    """POST /provider should return 409 if provider exists."""
    with patch("routes.create_provider", return_value=(None, "Provider exists")):
        rv = client.post("/provider", json={"name": "Test"})
        assert rv.status_code == 409
        assert rv.json == {"error": "Provider exists"}

def test_update_provider_success(client):
    """PUT /provider/<id> should return 200 if update is successful."""
    with patch("routes.update_provider", return_value=(True, None)):
        rv = client.put("/provider/1", json={"name": "NewName"})
        assert rv.status_code == 200
        assert rv.json == {"message": "updated"}

def test_update_provider_not_found(client):
    """PUT /provider/<id> should return 404 if provider not found."""
    with patch("routes.update_provider", return_value=(False, "Provider not found")):
        rv = client.put("/provider/999", json={"name": "NewName"})
        assert rv.status_code == 404
        assert "not found" in rv.json["error"].lower()

def test_update_provider_conflict(client):
    """PUT /provider/<id> should return 409 if name conflict occurs."""
    with patch("routes.update_provider", return_value=(False, "Name conflict")):
        rv = client.put("/provider/1", json={"name": "ConflictName"})
        assert rv.status_code == 409
        assert "conflict" in rv.json["error"].lower()

# ------------------------
# Rates Routes
# ------------------------

def test_get_rates_success(client):
    """GET /rates should call send_file without accessing disk."""
    # Patch get_rates_file_path to return fake path (no real file needed)
    with patch("routes.get_rates_file_path", return_value=("/tmp/rates.xlsx", None)):
        # Patch send_file imported in routes.py – THIS IS CRUCIAL
        with patch("routes.send_file", return_value=MagicMock()) as mock_send:
            rv = client.get("/rates")
            # Ensure send_file was called once
            mock_send.assert_called_once()

def test_post_rates_missing_file(client):
    """POST /rates should return 400 if file parameter is missing."""
    rv = client.post("/rates", json={})
    assert rv.status_code == 400
    assert "file parameter required" in rv.json["error"]


def test_post_rates_error(client):
    """POST /rates should return 400 if upload_rates raises ValueError."""
    with patch("routes.upload_rates", side_effect=ValueError("Invalid file")):
        rv = client.post("/rates", json={"file": "bad.xlsx"})
        assert rv.status_code == 400
        assert "invalid file" in rv.json["error"].lower()

def test_get_rates_success(client):
    with patch("routes.get_rates_file_path", return_value=("/tmp/rates.xlsx", None)):
        with patch("routes.send_file", return_value=MagicMock()) as mock_send:
            rv = client.get("/rates")
            mock_send.assert_called_once()

def test_get_rates_not_found(client):
    """GET /rates should return 404 if file not found."""
    with patch("routes.get_rates_file_path", return_value=(None, "File not found")):
        rv = client.get("/rates")
        assert rv.status_code == 404
        assert "file not found" in rv.json["error"].lower()

# ------------------------
# Truck Routes
# ------------------------
def test_get_truck_success(client):
    """GET /truck/<id> should return truck data if found."""
    mock_data = {"id": "T1", "provider": 1}
    with patch("routes.get_truck", return_value=(mock_data, None)):
        rv = client.get("/truck/T1")
        assert rv.status_code == 200
        assert rv.json == mock_data

def test_get_truck_not_found(client):
    """GET /truck/<id> should return 404 if truck not found."""
    with patch("routes.get_truck", return_value=(None, "Truck not found")):
        rv = client.get("/truck/T99")
        assert rv.status_code == 404
        assert "truck not found" in rv.json["error"].lower()

def test_create_truck_success(client):
    """POST /truck should succeed if id and provider are valid."""
    with patch("routes.create_truck", return_value=(True, None)):
        rv = client.post("/truck", json={"id": "T1", "provider": 1})
        assert rv.status_code != 400  # passed initial validation

def test_create_truck_missing_fields(client):
    """POST /truck should return 400 if required fields missing."""
    rv = client.post("/truck", json={"id": "T1"})
    assert rv.status_code == 400
    assert "truck id and provider id required" in rv.json["error"]

def test_update_truck_success(client):
    """PUT /truck/<id> should return 200 if update successful."""
    with patch("routes.update_truck", return_value=(True, None)):
        rv = client.put("/truck/T1", json={"provider": 2})
        assert rv.status_code == 200
        assert rv.json == {"id": "T1", "provider": 2}

def test_update_truck_missing_provider(client):
    """PUT /truck/<id> should return 400 if provider id missing."""
    rv = client.put("/truck/T1", json={})
    assert rv.status_code == 400
    assert "provider id required" in rv.json["error"]

def test_update_truck_not_found(client):
    """PUT /truck/<id> should return 404 if truck not found."""
    with patch("routes.update_truck", return_value=(False, "Truck not found")):
        rv = client.put("/truck/T99", json={"provider": 2})
        assert rv.status_code == 404
        assert "truck not found" in rv.json["error"].lower()