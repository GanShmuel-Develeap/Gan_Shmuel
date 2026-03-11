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