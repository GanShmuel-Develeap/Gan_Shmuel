import pytest
from unittest.mock import patch
import billing.utils as utils

# Mock data
MOCK_TRUCK_ID = 'T123'
MOCK_PROVIDER_ID = 1
MOCK_TRUCK_DATA = {"id": MOCK_TRUCK_ID, "tara": 1000, "sessions": [1, 2, 3]}

# ---- create_truck ----
def test_create_truck_success():
    with patch('billing.utils.get_connection') as mock_conn:
        mock_cursor = mock_conn.return_value.cursor.return_value
        # Provider exists, truck does not exist
        mock_cursor.fetchone.side_effect = [True, None]
        mock_cursor.lastrowid = 42
        result, err = utils.create_truck(MOCK_TRUCK_ID, MOCK_PROVIDER_ID)
        assert result is True
        assert err is None


def test_create_truck_provider_not_found():
    with patch('billing.utils.get_connection') as mock_conn:
        mock_cursor = mock_conn.return_value.cursor.return_value
        # Provider does not exist
        mock_cursor.fetchone.side_effect = [None]
        result, err = utils.create_truck(MOCK_TRUCK_ID, MOCK_PROVIDER_ID)
        assert result is False
        assert err == "Provider not found"


def test_create_truck_already_exists():
    with patch('billing.utils.get_connection') as mock_conn:
        mock_cursor = mock_conn.return_value.cursor.return_value
        # Provider exists, truck exists
        mock_cursor.fetchone.side_effect = [True, True]
        result, err = utils.create_truck(MOCK_TRUCK_ID, MOCK_PROVIDER_ID)
        assert result is False
        assert err == "Truck already exists"

# ---- update_truck ----
def test_update_truck_success():
    with patch('billing.utils.get_connection') as mock_conn:
        mock_cursor = mock_conn.return_value.cursor.return_value
        # Truck exists, provider exists
        mock_cursor.fetchone.side_effect = [True, True]
        result, err = utils.update_truck(MOCK_TRUCK_ID, MOCK_PROVIDER_ID)
        assert result is True
        assert err is None


def test_update_truck_not_found():
    with patch('billing.utils.get_connection') as mock_conn:
        mock_cursor = mock_conn.return_value.cursor.return_value
        # Truck does not exist
        mock_cursor.fetchone.side_effect = [None]
        result, err = utils.update_truck(MOCK_TRUCK_ID, MOCK_PROVIDER_ID)
        assert result is False
        assert err == "Truck not found"


def test_update_truck_provider_not_found():
    with patch('billing.utils.get_connection') as mock_conn:
        mock_cursor = mock_conn.return_value.cursor.return_value
        # Truck exists, provider does not exist
        mock_cursor.fetchone.side_effect = [True, None]
        result, err = utils.update_truck(MOCK_TRUCK_ID, MOCK_PROVIDER_ID)
        assert result is False
        assert err == "Provider not found"

# ---- get_truck ----
def test_get_truck_success():
    with patch('billing.utils.get_bill_connection') as mock_bill_conn, \
         patch('billing.utils.get_weight_connection') as mock_weight_conn:
        # Bill DB: truck exists
        bill_cursor = mock_bill_conn.return_value.cursor.return_value
        bill_cursor.fetchone.return_value = {"id": MOCK_TRUCK_ID}
        # Weight DB: sessions and tara
        weight_cursor = mock_weight_conn.return_value.cursor.return_value
        weight_cursor.fetchall.return_value = [{"id": 1}, {"id": 2}, {"id": 3}]
        weight_cursor.fetchone.return_value = {"truckTara": 1000}
        data, err = utils.get_truck(MOCK_TRUCK_ID)
        assert err is None
        assert data["id"] == MOCK_TRUCK_ID
        assert data["tara"] == 1000
        assert data["sessions"] == [1, 2, 3]

def test_get_truck_not_found():
    with patch('billing.utils.get_bill_connection') as mock_bill_conn:
        bill_cursor = mock_bill_conn.return_value.cursor.return_value
        bill_cursor.fetchone.return_value = None
        data, err = utils.get_truck(MOCK_TRUCK_ID)
        assert data is None
        assert err == "Truck not found"


#### RUN TESTS:
#### python3 -m pytest -v billing/test/test_utils.py 