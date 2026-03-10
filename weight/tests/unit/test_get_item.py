from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../weight-app')))

from main import app


class FakeCursor:
    def __init__(self, results):
        self.results = list(results)
        self.current_result = None
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append((query, params))
        if not self.results:
            raise AssertionError("No mocked DB result left for execute()")
        self.current_result = self.results.pop(0)

    def fetchone(self):
        if self.current_result is None:
            raise AssertionError("fetchone() called before execute()")
        return self.current_result.get("fetchone")

    def fetchall(self):
        if self.current_result is None:
            raise AssertionError("fetchall() called before execute()")
        return self.current_result.get("fetchall", [])

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.closed = False

    def cursor(self, dictionary=False):
        assert dictionary is True
        return self._cursor

    def close(self):
        self.closed = True


def client():
    return app.test_client()


# -------------------------
# Route contract tests
# -------------------------

@patch("main.get_item_data")
def test_get_item_calls_service_with_default_args(mock_service):
    mock_service.return_value = {
        "id": "TRUCK-1",
        "tara": 12000,
        "sessions": [1, 2]
    }

    resp = client().get("/item/TRUCK-1")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data == {
        "id": "TRUCK-1",
        "tara": 12000,
        "sessions": [1, 2]
    }

    mock_service.assert_called_once_with("TRUCK-1", None, None)


@patch("main.get_item_data")
def test_get_item_passes_time_args_to_service(mock_service):
    mock_service.return_value = {
        "id": "TRUCK-9",
        "tara": "na",
        "sessions": []
    }

    resp = client().get("/item/TRUCK-9?from=20260301000000&to=20260310120000")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["id"] == "TRUCK-9"

    mock_service.assert_called_once_with(
        "TRUCK-9",
        "20260301000000",
        "20260310120000"
    )


@patch("main.get_item_data")
def test_get_item_returns_404_when_service_returns_none(mock_service):
    mock_service.return_value = None

    resp = client().get("/item/UNKNOWN")
    data = resp.get_json()

    assert resp.status_code == 404
    assert data == {"error": "item not found"}

    mock_service.assert_called_once_with("UNKNOWN", None, None)


# -------------------------
# Behavior tests
# -------------------------

@patch("services.item_service.get_conn")
def test_get_item_truck_success(mock_get_conn):
    cursor = FakeCursor([
        {"fetchone": {"exists": 1}},  # truck exists
        {"fetchall": [{"session_id": 1}, {"session_id": 2}]},  # sessions
        {"fetchone": {"truckTara": 12000}},  # tara
    ])
    conn = FakeConnection(cursor)
    mock_get_conn.return_value = conn

    resp = client().get("/item/TRUCK-1?from=20260301000000&to=20260310120000")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data == {
        "id": "TRUCK-1",
        "tara": 12000,
        "sessions": [1, 2],
    }

    assert len(cursor.executed) == 3
    assert cursor.closed
    assert conn.closed


@patch("services.item_service.get_conn")
def test_get_item_container_success(mock_get_conn):
    cursor = FakeCursor([
        {"fetchone": None},  # truck not found
        {"fetchone": {"exists": 1}},  # container exists
        {"fetchall": [{"session_id": 7}, {"session_id": 9}]},
    ])
    conn = FakeConnection(cursor)
    mock_get_conn.return_value = conn

    resp = client().get("/item/CONT-001?from=20260301000000&to=20260310120000")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data == {
        "id": "CONT-001",
        "tara": "na",
        "sessions": [7, 9],
    }

    assert len(cursor.executed) == 3


@patch("services.item_service.get_conn")
def test_get_item_not_found(mock_get_conn):
    cursor = FakeCursor([
        {"fetchone": None},  # truck not found
        {"fetchone": None},  # container not found
    ])
    conn = FakeConnection(cursor)
    mock_get_conn.return_value = conn

    resp = client().get("/item/NO-SUCH-ID?from=20260301000000&to=20260310120000")
    data = resp.get_json()

    assert resp.status_code == 404
    assert data == {"error": "item not found"}

    assert len(cursor.executed) == 2


@patch("services.item_service.get_conn")
def test_get_item_existing_truck_but_no_sessions_in_range(mock_get_conn):
    cursor = FakeCursor([
        {"fetchone": {"exists": 1}},  # truck exists
        {"fetchall": []},  # no sessions
        {"fetchone": None},  # no tara
    ])
    conn = FakeConnection(cursor)
    mock_get_conn.return_value = conn

    resp = client().get("/item/TRUCK-EMPTY?from=20260301000000&to=20260310120000")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data == {
        "id": "TRUCK-EMPTY",
        "tara": "na",
        "sessions": [],
    }


@patch("services.item_service.get_conn")
def test_get_item_truck_precedence_over_container(mock_get_conn):
    cursor = FakeCursor([
        {"fetchone": {"exists": 1}},  # truck exists
        {"fetchall": [{"session_id": 3}]},
        {"fetchone": {"truckTara": 9000}},
    ])
    conn = FakeConnection(cursor)
    mock_get_conn.return_value = conn

    resp = client().get("/item/SAME-ID?from=20260301000000&to=20260310120000")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data == {
        "id": "SAME-ID",
        "tara": 9000,
        "sessions": [3],
    }