import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch


# ===========================================================================  
# Fixtures
# ===========================================================================  

@pytest.fixture
def mock_db():
    """Patches get_connection and yields (cursor, conn) to each test."""
    cursor = MagicMock()
    conn = MagicMock()
    conn.cursor.return_value = cursor
    conn.is_connected.return_value = True
    with patch("utils.get_connection", return_value=conn):
        yield cursor, conn


@pytest.fixture
def mock_api():
    with patch("utils.api_client.get_item") as m:
        yield m


def set_fetchone(cursor, *rows):
    """Configure cursor.fetchone to return rows sequentially."""
    cursor.fetchone.side_effect = list(rows)


# ===========================================================================  
# health_check
# ===========================================================================  

class TestHealthCheck:

    def test_returns_true_when_connected(self, mock_db):
        from utils import health_check
        assert health_check() is True

    def test_returns_false_when_not_connected(self, mock_db):
        _, conn = mock_db
        conn.is_connected.return_value = False
        from utils import health_check
        assert health_check() is False

    def test_returns_false_on_exception(self):
        with patch("utils.get_connection", side_effect=Exception("DB error")):
            from utils import health_check
            assert health_check() is False


# ===========================================================================  
# create_provider
# ===========================================================================  

class TestCreateProvider:

    def test_creates_new_provider(self, mock_db):
        cursor, _ = mock_db
        set_fetchone(cursor, None)
        cursor.lastrowid = 42
        from utils import create_provider
        provider_id, err = create_provider("Acme")
        assert provider_id == 42
        assert err is None

    def test_rejects_duplicate_name(self, mock_db):
        cursor, _ = mock_db
        set_fetchone(cursor, {"id": 1})
        from utils import create_provider
        provider_id, err = create_provider("Acme")
        assert provider_id is None
        assert "already exists" in err


# ===========================================================================  
# update_provider
# ===========================================================================  

class TestUpdateProvider:

    def test_updates_existing_provider(self, mock_db):
        cursor, _ = mock_db
        set_fetchone(cursor, {"id": 1}, None)
        from utils import update_provider
        ok, err = update_provider(1, "NewName")
        assert ok is True
        assert err is None

    def test_returns_error_when_provider_not_found(self, mock_db):
        cursor, _ = mock_db
        set_fetchone(cursor, None)
        from utils import update_provider
        ok, err = update_provider(99, "NewName")
        assert ok is False
        assert "not found" in err

    def test_returns_error_when_name_already_taken(self, mock_db):
        cursor, _ = mock_db
        set_fetchone(cursor, {"id": 1}, {"id": 2})
        from utils import update_provider
        ok, err = update_provider(1, "TakenName")
        assert ok is False
        assert "already taken" in err


# ===========================================================================  
# _validate_rates
# ===========================================================================  

class TestValidateRates:

    def _df(self, data):
        return pd.DataFrame(data)

    def test_valid_dataframe_passes(self):
        from utils import _validate_rates
        result = _validate_rates(self._df({"Product": ["apples"], "Rate": [100], "Scope": [None]}))
        assert result["Rate"].iloc[0] == 100

    def test_raises_on_empty_dataframe(self):
        from utils import _validate_rates
        with pytest.raises(ValueError, match="no data rows"):
            _validate_rates(pd.DataFrame({"Product": [], "Rate": [], "Scope": []}))

    def test_raises_on_missing_product(self):
        from utils import _validate_rates
        with pytest.raises(ValueError, match="Missing Product"):
            _validate_rates(self._df({"Product": [None], "Rate": [10], "Scope": [None]}))

    def test_raises_on_missing_rate(self):
        from utils import _validate_rates
        with pytest.raises(ValueError, match="Missing Rate"):
            _validate_rates(self._df({"Product": ["apples"], "Rate": [None], "Scope": [None]}))

    def test_raises_on_non_numeric_rate(self):
        from utils import _validate_rates
        with pytest.raises(ValueError, match="Non-numeric Rate"):
            _validate_rates(self._df({"Product": ["apples"], "Rate": ["abc"], "Scope": [None]}))

    def test_scope_all_becomes_none(self):
        from utils import _validate_rates
        result = _validate_rates(self._df({"Product": ["apples"], "Rate": [50], "Scope": ["All"]}))
        assert result["Scope"].iloc[0] is None

    def test_scope_numeric_id_is_kept(self):
        from utils import _validate_rates
        result = _validate_rates(self._df({"Product": ["apples"], "Rate": [50], "Scope": [3]}))
        assert result["Scope"].iloc[0] == 3

    def test_scope_invalid_string_raises(self):
        from utils import _validate_rates
        with pytest.raises(ValueError, match="Invalid Scope"):
            _validate_rates(self._df({"Product": ["apples"], "Rate": [50], "Scope": ["bad"]}))

    def test_product_names_are_stripped(self):
        from utils import _validate_rates
        result = _validate_rates(self._df({"Product": ["  apples  "], "Rate": [10], "Scope": [None]}))
        assert result["Product"].iloc[0] == "apples"

    def test_rate_is_converted_to_int(self):
        from utils import _validate_rates
        result = _validate_rates(self._df({"Product": ["apples"], "Rate": [9.9], "Scope": [None]}))
        assert result["Rate"].iloc[0] == 9
        assert isinstance(result["Rate"].iloc[0], (int, np.integer))


# ===========================================================================  
# upload_rates
# ===========================================================================  

VALID_RATES_DF = pd.DataFrame({
    "Product": ["apples", "oranges"],
    "Rate": [100, 200],
    "Scope": [None, None],
})


class TestUploadRates:

    def test_returns_error_when_in_folder_missing(self, mock_db):
        with patch("utils.os.path.isdir", return_value=False):
            from utils import upload_rates
            count, err = upload_rates("rates.xlsx")
            assert count is None
            assert "/in folder" in err

    def test_returns_error_when_file_missing(self, mock_db):
        with patch("utils.os.path.isdir", return_value=True), \
             patch("utils.os.path.isfile", return_value=False):
            from utils import upload_rates
            count, err = upload_rates("missing.xlsx")
            assert count is None
            assert "not found" in err

    def test_inserts_rows_and_returns_count(self, mock_db):
        cursor, _ = mock_db
        with patch("utils.os.path.isdir", return_value=True), \
             patch("utils.os.path.isfile", return_value=True), \
             patch("utils.pd.read_excel", return_value=VALID_RATES_DF):
            from utils import upload_rates
            count, err = upload_rates("rates.xlsx")
            assert count == 2
            assert err is None
            cursor.execute.assert_any_call("DELETE FROM Rates")
            cursor.executemany.assert_called_once()

    def test_rollback_on_db_error(self, mock_db):
        cursor, conn = mock_db
        cursor.executemany.side_effect = Exception("DB insert failed")
        with patch("utils.os.path.isdir", return_value=True), \
             patch("utils.os.path.isfile", return_value=True), \
             patch("utils.pd.read_excel", return_value=VALID_RATES_DF):
            from utils import upload_rates
            with pytest.raises(Exception, match="DB insert failed"):
                upload_rates("rates.xlsx")
            conn.rollback.assert_called_once()

    def test_returns_error_on_unreadable_excel(self, mock_db):
        with patch("utils.os.path.isdir", return_value=True), \
             patch("utils.os.path.isfile", return_value=True), \
             patch("utils.pd.read_excel", side_effect=Exception("bad file")):
            from utils import upload_rates
            count, err = upload_rates("corrupt.xlsx")
            assert count is None
            assert "Failed to read" in err


# ===========================================================================  
# get_rates_file_path
# ===========================================================================  

class TestGetRatesFilePath:

    def test_returns_most_recently_modified_file(self):
        with patch("utils.os.listdir", return_value=["rates_old.xlsx", "rates_new.xlsx"]), \
             patch("utils.os.path.getmtime", side_effect=[500, 1000]):
            from utils import get_rates_file_path
            path, err = get_rates_file_path()
            assert err is None
            assert "rates_new.xlsx" in path

    def test_returns_error_when_no_xlsx_files(self):
        with patch("utils.os.listdir", return_value=["readme.txt", "data.csv"]):
            from utils import get_rates_file_path
            path, err = get_rates_file_path()
            assert path is None
            assert "No rates files" in err


# ===========================================================================  
# create_truck
# ===========================================================================  

class TestCreateTruck:

    def test_creates_truck_successfully(self, mock_db):
        cursor, _ = mock_db
        set_fetchone(cursor, {"id": 1}, None)
        from utils import create_truck
        ok, err = create_truck("T-001", 1)
        assert ok is True
        assert err is None

    def test_returns_error_when_provider_not_found(self, mock_db):
        cursor, _ = mock_db
        set_fetchone(cursor, None)
        from utils import create_truck
        ok, err = create_truck("T-001", 99)
        assert ok is False
        assert "Provider not found" in err

    def test_returns_error_when_truck_already_exists(self, mock_db):
        cursor, _ = mock_db
        set_fetchone(cursor, {"id": 1}, {"id": "T-001"})
        from utils import create_truck
        ok, err = create_truck("T-001", 1)
        assert ok is False
        assert "already exists" in err


# ===========================================================================  
# update_truck
# ===========================================================================  

class TestUpdateTruck:

    def test_updates_truck_successfully(self, mock_db):
        cursor, _ = mock_db
        set_fetchone(cursor, {"id": "T-001"}, {"id": 2})
        from utils import update_truck
        ok, err = update_truck("T-001", 2)
        assert ok is True
        assert err is None

    def test_returns_error_when_truck_not_found(self, mock_db):
        cursor, _ = mock_db
        set_fetchone(cursor, None)
        from utils import update_truck
        ok, err = update_truck("GHOST", 1)
        assert ok is False
        assert "Truck not found" in err

    def test_returns_error_when_new_provider_not_found(self, mock_db):
        cursor, _ = mock_db
        set_fetchone(cursor, {"id": "T-001"}, None)
        from utils import update_truck
        ok, err = update_truck("T-001", 99)
        assert ok is False
        assert "Provider not found" in err


# ===========================================================================  
# get_truck
# ===========================================================================  

class TestGetTruck:

    def test_returns_truck_with_sessions(self, mock_db, mock_api):
        cursor, _ = mock_db
        set_fetchone(cursor, {"id": "T-001"})
        mock_api.return_value = ({"tara": 5000, "sessions": [{"id": 1}]}, None)
        from utils import get_truck
        result, err = get_truck("T-001")
        assert err is None
        assert result["id"] == "T-001"
        assert result["tara"] == 5000
        assert len(result["sessions"]) == 1

    def test_returns_error_when_truck_not_in_db(self, mock_db):
        cursor, _ = mock_db
        set_fetchone(cursor, None)
        from utils import get_truck
        result, err = get_truck("GHOST")
        assert result is None
        assert "not found" in err

    

    def test_returns_error_when_weight_api_fails(self, mock_db, mock_api):
        cursor, _ = mock_db
        set_fetchone(cursor, {"id": "T-001"})
        mock_api.return_value = (None, "weight system error")
        from utils import get_truck
        result, err = get_truck("T-001")
        assert result is None
        assert "not found in weight system" in err

# ===========================================================================  
# get_provider_name
# ===========================================================================  

class TestGetProviderName:
    def test_returns_name_if_exists(self, mock_db):
        cursor, _ = mock_db
        # Mock fetchone to return a tuple containing the name
        cursor.fetchone.return_value = ("Acme Corp",)
        from utils import get_provider_name
        assert get_provider_name(1) == "Acme Corp"

    def test_returns_false_if_not_exists(self, mock_db):
        cursor, _ = mock_db
        cursor.fetchone.return_value = None
        from utils import get_provider_name
        assert get_provider_name(999) is False

# ===========================================================================  
# get_rates_for_provider
# ===========================================================================  

class TestGetRatesForProvider:
    def test_correctly_overrides_global_rates(self, mock_db):
        cursor, _ = mock_db
        # Mock two rows: one global (scope None) and one specific to provider 1
        cursor.fetchall.return_value = [
            {'product_name': 'Apples', 'scope': None, 'rate': 10},
            {'product_name': 'Apples', 'scope': 1, 'rate': 15},
            {'product_name': 'Bananas', 'scope': None, 'rate': 5}
        ]
        from utils import get_rates_for_provider
        rates, err = get_rates_for_provider(1)
        assert err is None
        assert rates['Apples'] == 15  # Specific override
        assert rates['Bananas'] == 5 # Global fallback

# ===========================================================================  
# get_valid_trucks
# ===========================================================================  

class TestGetValidTrucks:
    def test_filters_trucks_by_db_presence(self, mock_db):
        cursor, _ = mock_db
        # Input weights from API
        weight_list = [
            {'truck_id': 'T1'}, {'truck_id': 'T2'}, {'truck_id': 'T3'}
        ]
        # Only T1 and T2 exist in DB for this provider
        cursor.fetchall.return_value = [('T1',), ('T2',)]
        
        from utils import get_valid_trucks
        result = get_valid_trucks(weight_list, 1)
        
        assert len(result) == 2
        assert any(t['truck_id'] == 'T1' for t in result)
        assert not any(t['truck_id'] == 'T3' for t in result)

# ===========================================================================  
# get_bill_data (Integration-style Utility Test)
# ===========================================================================  

class TestGetBillData:
    @patch("utils.get_provider_name")
    @patch("utils.api_client.get_weights")
    @patch("utils.get_rates_for_provider")
    @patch("utils.get_valid_trucks")
    def test_calculates_total_correctly(self, mock_valid, mock_rates, mock_weights, mock_name):
        # Setup Mocks
        mock_name.return_value = "Test Provider"
        mock_weights.return_value = ([], None) # weight_data handled by mock_valid
        mock_rates.return_value = ({"Apples": 10}, None)
        
        # Simulate 2 trips of Apples with 100kg each
        mock_valid.return_value = [
            {'truck_id': 'T1', 'produce': 'Apples', 'neto': 100},
            {'truck_id': 'T1', 'produce': 'Apples', 'neto': 100}
        ]

        from utils import get_bill_data
        data, err = get_bill_data(1)

        assert err is None
        assert data['name'] == "Test Provider"
        assert data['truckCount'] == 1 # Only T1
        assert data['sessionCount'] == 2
        assert data['total'] == 2000 # (100+100) * 10
        assert data['products'][0]['product'] == 'Apples'
        assert data['products'][0]['pay'] == 2000

    def test_returns_error_if_provider_missing(self, mock_db):
        with patch("utils.get_provider_name", return_value=False):
            from utils import get_bill_data
            data, err = get_bill_data(999)
            assert data is None
            assert err == "Provider not found"